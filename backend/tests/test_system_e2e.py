from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.system


@pytest.mark.asyncio
async def test_complete_clinical_flow_end_to_end(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coordinador E2E")
    tutor = await create_user("tutor", full_name="Tutor E2E")
    student = await create_user("student", full_name="Estudiante E2E")

    cohort_resp = await client.post(
        "/dashboard/cohorts",
        json={"year": 2026, "semester": 1, "name": "Cohorte Sistema"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert cohort_resp.status_code == 201, cohort_resp.text
    cohort_id = cohort_resp.json()["id"]

    assignment_resp = await client.post(
        "/dashboard/assignments",
        json={
            "student_id": str(student.id),
            "tutor_id": str(tutor.id),
            "cohort_id": cohort_id,
            "care_level": "primary",
            "clinical_site": "Hospital Universitario",
            "start_date": str(date(2026, 1, 1)),
            "end_date": str(date(2026, 6, 30)),
        },
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert assignment_resp.status_code == 201, assignment_resp.text
    assignment_id = assignment_resp.json()["id"]

    attendance_resp = await client.post(
        "/attendance",
        json={"date": "2026-04-14", "status": "present", "observation": "Turno mañana"},
        headers=auth_headers(str(student.id), "student"),
    )
    assert attendance_resp.status_code == 201, attendance_resp.text

    logbook_resp = await client.post(
        "/logbook/entries",
        json={
            "cohort_id": cohort_id,
            "week_number": 5,
            "week_start_date": "2026-04-13",
            "wellbeing_status": "regular",
            "procedures": [
                {
                    "name": "Examen y diagnóstico",
                    "description": "Paciente de control",
                    "quantity": 2,
                }
            ],
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert logbook_resp.status_code == 201, logbook_resp.text

    my_students_resp = await client.get(
        "/evaluations/my-students",
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert my_students_resp.status_code == 200, my_students_resp.text
    assert any(s["id"] == str(student.id) for s in my_students_resp.json())

    evaluation_resp = await client.post(
        "/evaluations",
        json={
            "student_id": str(student.id),
            "assignment_id": assignment_id,
            "period_label": "Semana 5",
            "overall_comment": "Avance esperado",
            "items": [
                {"dimension": "Actitud", "score": 5, "comment": "Muy buena"},
                {"dimension": "Técnica", "score": 3, "comment": "Debe mejorar"},
            ],
        },
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert evaluation_resp.status_code == 201, evaluation_resp.text

    student_eval_resp = await client.get(
        f"/evaluations/students/{student.id}",
        headers=auth_headers(str(student.id), "student"),
    )
    assert student_eval_resp.status_code == 200, student_eval_resp.text
    assert len(student_eval_resp.json()) == 1

    incident_resp = await client.post(
        "/incidents",
        json={
            "incident_type": "other",
            "description": "Situación reportada por estudiante",
            "event_date": "2026-04-14",
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert incident_resp.status_code == 201, incident_resp.text
    incident_id = incident_resp.json()["id"]

    incidents_resp = await client.get(
        "/incidents",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert incidents_resp.status_code == 200, incidents_resp.text
    assert len(incidents_resp.json()) >= 1

    review_resp = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "under_review"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert review_resp.status_code == 200, review_resp.text

    alert_run_resp = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert alert_run_resp.status_code == 200, alert_run_resp.text

    summary_resp = await client.get(
        "/alerts/summary",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()
    assert summary["red"] >= 1

    activity_resp = await client.get(
        "/dashboard/recent-activity?limit=10",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert activity_resp.status_code == 200, activity_resp.text
    items = activity_resp.json()["items"]
    assert any(item["kind"] == "incident_created" for item in items)
    assert any(item["kind"] == "logbook_created" for item in items)
    assert any(item["kind"] == "evaluation_created" for item in items)
