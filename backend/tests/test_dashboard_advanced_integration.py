from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select

import app.core.keycloak_client as keycloak_client
from app.models.assignment import Assignment
from app.models.user import User


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_dashboard_trends_activity_wellbeing_and_metric_series(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coord Metrics")
    tutor = await create_user("tutor", full_name="Tutor Metrics")
    student = await create_user("student", full_name="Student Metrics")
    cohort = await create_cohort(name="Cohorte Metrics")

    assignment = await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    logbook_resp = await client.post(
        "/logbook/entries",
        json={
            "cohort_id": str(cohort.id),
            "week_number": 6,
            "week_start_date": "2026-04-14",
            "wellbeing_status": "regular",
            "procedures": [
                {
                    "name": "Examen y diagnóstico",
                    "description": "Registro para actividad",
                    "quantity": 1,
                }
            ],
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert logbook_resp.status_code == 201, logbook_resp.text

    eval_resp = await client.post(
        "/evaluations",
        json={
            "student_id": str(student.id),
            "assignment_id": str(assignment.id),
            "period_label": "Semana 6",
            "overall_comment": "OK",
            "items": [{"dimension": "Actitud", "score": 5, "comment": None}],
        },
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert eval_resp.status_code == 201, eval_resp.text

    incident_resp = await client.post(
        "/incidents",
        json={
            "incident_type": "other",
            "description": "Incidente para dashboard",
            "event_date": "2026-04-14",
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert incident_resp.status_code == 201, incident_resp.text

    run_alerts = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert run_alerts.status_code == 200, run_alerts.text

    trends = await client.get(
        "/dashboard/overview-trends",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert trends.status_code == 200, trends.text
    trend_keys = set(trends.json().keys())
    assert {
        "total_students",
        "total_tutors",
        "total_entries",
        "pending_entries",
        "total_incidents",
        "open_incidents",
    }.issubset(trend_keys)

    activity = await client.get(
        "/dashboard/recent-activity?limit=10",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert activity.status_code == 200, activity.text
    kinds = {item["kind"] for item in activity.json()["items"]}
    assert "logbook_created" in kinds
    assert "evaluation_created" in kinds
    assert "incident_created" in kinds

    wellbeing_quick = await client.get(
        "/dashboard/wellbeing-quick?limit=5",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert wellbeing_quick.status_code == 200, wellbeing_quick.text
    assert wellbeing_quick.json()["total_active"] >= 1

    metric_series = await client.get(
        "/dashboard/metric-series",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert metric_series.status_code == 200, metric_series.text
    series = metric_series.json()["series"]
    assert len(series) == 4
    assert all(len(item["points"]) == 4 for item in series)


@pytest.mark.asyncio
async def test_dashboard_tutor_create_list_update_flow(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coord Tutors")

    created = await client.post(
        "/dashboard/tutors",
        json={
            "email": "nuevo.tutor.dashboard@internado.cl",
            "full_name": "Tutor Dashboard Nuevo",
            "password": "ClaveSegura123",
            "profession": "Dentista",
            "available_hours_per_week": 12,
            "tutor_training_status": "yes",
        },
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert created.status_code == 201, created.text
    tutor_id = created.json()["id"]
    assert created.json()["profession"] == "Dentista"

    listed = await client.get(
        "/dashboard/tutors",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert listed.status_code == 200, listed.text
    assert any(t["id"] == tutor_id for t in listed.json())

    updated = await client.patch(
        f"/dashboard/tutors/{tutor_id}",
        json={
            "full_name": "Tutor Renombrado",
            "is_active": False,
            "profession": "Odontólogo",
            "available_hours_per_week": 8,
            "tutor_training_status": "in_progress",
        },
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["full_name"] == "Tutor Renombrado"
    assert updated.json()["is_active"] is False
    assert updated.json()["profession"] == "Odontólogo"


@pytest.mark.asyncio
async def test_dashboard_update_and_delete_student(
    client: AsyncClient,
    db_session,
    create_user,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    coordinator = await create_user("coordinator")
    student = await create_user("student", full_name="Student Delete")

    updated = await client.patch(
        f"/dashboard/students/{student.id}",
        json={"full_name": "Student Updated", "is_active": False},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["full_name"] == "Student Updated"

    monkeypatch.setattr(keycloak_client, "delete_keycloak_user", lambda user_id: None)

    deleted = await client.delete(
        f"/dashboard/students/{student.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert deleted.status_code == 204, deleted.text

    remaining = (await db_session.execute(select(User).where(User.id == student.id))).scalar_one_or_none()
    assert remaining is None


@pytest.mark.asyncio
async def test_dashboard_delete_tutor_deactivates_assignments(
    client: AsyncClient,
    db_session,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    coordinator = await create_user("coordinator")
    tutor = await create_user("tutor", full_name="Tutor Delete")
    student = await create_user("student", full_name="Student Linked")
    cohort = await create_cohort(name="Cohorte Tutor Delete")

    assignment = await create_assignment(student.id, tutor.id, cohort.id)

    monkeypatch.setattr(keycloak_client, "delete_keycloak_user", lambda user_id: None)

    deleted = await client.delete(
        f"/dashboard/tutors/{tutor.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert deleted.status_code == 204, deleted.text

    updated_assignment = (
        await db_session.execute(select(Assignment).where(Assignment.id == assignment.id))
    ).scalar_one()
    assert updated_assignment.is_active is False

    tutor_in_db = (await db_session.execute(select(User).where(User.id == tutor.id))).scalar_one_or_none()
    assert tutor_in_db is None
