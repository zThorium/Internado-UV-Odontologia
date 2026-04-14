from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_alerts_flow_incident_generates_red_and_can_be_resolved(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coordinador Alertas")
    tutor = await create_user("tutor", full_name="Tutor Alertas")
    student = await create_user("student", full_name="Estudiante Alertas")
    cohort = await create_cohort(name="Cohorte Alertas")

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    incident_resp = await client.post(
        "/incidents",
        json={
            "incident_type": "harassment",
            "description": "Incidente para disparar alerta",
            "event_date": "2026-04-11",
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert incident_resp.status_code == 201, incident_resp.text

    run_resp = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert run_resp.status_code == 200, run_resp.text
    run_data = run_resp.json()
    assert run_data["students_evaluated"] >= 1
    assert run_data["created"] >= 1

    summary_resp = await client.get(
        "/alerts/summary",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()
    assert summary["red"] >= 1

    students_resp = await client.get(
        "/alerts/students",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert students_resp.status_code == 200, students_resp.text
    students_data = students_resp.json()
    student_row = next(s for s in students_data if s["student_id"] == str(student.id))
    assert student_row["traffic_light"] == "red"
    assert any(alert["alert_type"] == "incident_report" for alert in student_row["active_alerts"])

    detail_resp = await client.get(
        f"/alerts/students/{student.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    assert len(detail["active_alerts"]) >= 1

    alert_id = detail["active_alerts"][0]["id"]
    resolve_resp = await client.post(
        f"/alerts/resolve/{alert_id}",
        json={"coordinator_note": "Caso gestionado"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    resolved = resolve_resp.json()
    assert resolved["is_active"] is False
    assert resolved["coordinator_note"] == "Caso gestionado"


@pytest.mark.asyncio
async def test_non_coordinator_cannot_access_alerts_endpoints(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    student = await create_user("student")

    run_resp = await client.post(
        "/alerts/run",
        headers=auth_headers(str(student.id), "student"),
    )
    assert run_resp.status_code == 403

    summary_resp = await client.get(
        "/alerts/summary",
        headers=auth_headers(str(student.id), "student"),
    )
    assert summary_resp.status_code == 403
