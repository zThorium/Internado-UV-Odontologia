from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.wellbeing import WellbeingAlert


pytestmark = pytest.mark.integration


def _logbook_payload(cohort_id: str, week_number: int, wellbeing_status: str) -> dict:
    return {
        "cohort_id": cohort_id,
        "week_number": week_number,
        "week_start_date": str(date(2026, 1, 1 + (week_number - 1) * 7)),
        "wellbeing_status": wellbeing_status,
        "procedures": [
            {"name": "Examen y diagnóstico", "description": "Seguimiento", "quantity": 1}
        ],
    }


@pytest.mark.asyncio
async def test_student_and_coordinator_wellbeing_endpoints(
    client: AsyncClient,
    db_session,
    create_user,
    create_cohort,
    auth_headers,
):
    student = await create_user("student", full_name="Estudiante Bienestar")
    coordinator = await create_user("coordinator", full_name="Coord Bienestar")
    cohort = await create_cohort(name="Cohorte Bienestar")

    first = await client.post(
        "/logbook/entries",
        json=_logbook_payload(str(cohort.id), week_number=1, wellbeing_status="difficult"),
        headers=auth_headers(str(student.id), "student"),
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/logbook/entries",
        json=_logbook_payload(str(cohort.id), week_number=2, wellbeing_status="difficult"),
        headers=auth_headers(str(student.id), "student"),
    )
    assert second.status_code == 201, second.text

    history_resp = await client.get(
        "/logbook/wellbeing/history",
        headers=auth_headers(str(student.id), "student"),
    )
    assert history_resp.status_code == 200, history_resp.text
    history = history_resp.json()
    assert len(history) == 2
    assert history[0]["week_number"] == 1
    assert history[1]["week_number"] == 2

    summary_resp = await client.get(
        "/logbook/wellbeing/coordinator-summary",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert summary_resp.status_code == 200, summary_resp.text
    summary = summary_resp.json()
    assert summary["red"] >= 1

    students_resp = await client.get(
        "/logbook/wellbeing/students",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert students_resp.status_code == 200, students_resp.text
    assert any(s["student_id"] == str(student.id) for s in students_resp.json())

    student_history_resp = await client.get(
        f"/logbook/wellbeing/students/{student.id}/history",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert student_history_resp.status_code == 200, student_history_resp.text
    assert len(student_history_resp.json()) == 2

    alert = (
        await db_session.execute(
            select(WellbeingAlert)
            .where(WellbeingAlert.student_id == student.id, WellbeingAlert.resolved.is_(False))
            .order_by(WellbeingAlert.triggered_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    assert alert is not None

    resolve_resp = await client.post(
        f"/logbook/wellbeing/alerts/{alert.id}/resolve",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    assert resolve_resp.json()["resolved"] is True
