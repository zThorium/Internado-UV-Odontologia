from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.acceptance


@pytest.mark.asyncio
async def test_ac01_logbook_review_flow_blocks_edits_after_review(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    """AC-01: Estudiante crea bitacora y coordinador puede revisarla, bloqueando edicion posterior."""
    coordinator = await create_user("coordinator")
    tutor = await create_user("tutor")
    student = await create_user("student")
    cohort = await create_cohort()

    await create_assignment(student.id, tutor.id, cohort.id)

    create_resp = await client.post(
        "/logbook/entries",
        json={
            "cohort_id": str(cohort.id),
            "week_number": 7,
            "week_start_date": "2026-04-13",
            "wellbeing_status": "good",
            "procedures": [{"name": "Examen y diagnóstico", "description": "", "quantity": 1}],
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert create_resp.status_code == 201, create_resp.text
    entry_id = create_resp.json()["id"]

    review_resp = await client.patch(
        f"/logbook/entries/{entry_id}/status",
        json={"status": "reviewed"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert review_resp.status_code == 200, review_resp.text

    blocked_edit = await client.put(
        f"/logbook/entries/{entry_id}",
        json={"procedures": [{"name": "Examen y diagnóstico", "description": "Ajuste", "quantity": 1}]},
        headers=auth_headers(str(student.id), "student"),
    )
    assert blocked_edit.status_code == 409


@pytest.mark.asyncio
async def test_ac02_tutor_can_evaluate_only_assigned_students(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    """AC-02: Tutor evalua solo estudiantes asignados; fuera de asignacion obtiene 403."""
    tutor = await create_user("tutor")
    student_assigned = await create_user("student", full_name="Asignado")
    student_other = await create_user("student", full_name="No Asignado")
    cohort = await create_cohort()

    assignment = await create_assignment(student_assigned.id, tutor.id, cohort.id)

    ok_eval = await client.post(
        "/evaluations",
        json={
            "student_id": str(student_assigned.id),
            "assignment_id": str(assignment.id),
            "period_label": "Semana 7",
            "overall_comment": "Correcto",
            "items": [{"dimension": "Actitud", "score": 5, "comment": None}],
        },
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert ok_eval.status_code == 201, ok_eval.text

    blocked_eval = await client.post(
        "/evaluations",
        json={
            "student_id": str(student_other.id),
            "assignment_id": str(uuid4()),
            "period_label": "Semana 7",
            "overall_comment": "No permitido",
            "items": [{"dimension": "Actitud", "score": 5, "comment": None}],
        },
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert blocked_eval.status_code == 403


@pytest.mark.asyncio
async def test_ac03_attendance_prevents_duplicates_same_date(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    """AC-03: No se permite duplicar asistencia del mismo estudiante en la misma fecha."""
    student = await create_user("student")
    payload = {"date": "2026-04-14", "status": "present", "observation": "ok"}

    first = await client.post(
        "/attendance",
        json=payload,
        headers=auth_headers(str(student.id), "student"),
    )
    assert first.status_code == 201, first.text

    duplicate = await client.post(
        "/attendance",
        json=payload,
        headers=auth_headers(str(student.id), "student"),
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_ac04_incident_lifecycle_student_to_coordinator_resolution(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    """AC-04: Incidente creado por estudiante puede pasar a under_review y resolved por coordinador."""
    student = await create_user("student")
    coordinator = await create_user("coordinator")

    created = await client.post(
        "/incidents",
        json={
            "incident_type": "abuse",
            "description": "Caso AC-04",
            "event_date": "2026-04-14",
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert created.status_code == 201, created.text
    incident_id = created.json()["id"]

    under_review = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "under_review"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert under_review.status_code == 200, under_review.text

    resolved = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "resolved"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_ac05_alerts_show_red_after_incident_and_can_be_resolved(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    """AC-05: Incidente activa semaforo rojo y la alerta se puede resolver."""
    coordinator = await create_user("coordinator")
    tutor = await create_user("tutor")
    student = await create_user("student")
    cohort = await create_cohort()

    await create_assignment(student.id, tutor.id, cohort.id)

    incident = await client.post(
        "/incidents",
        json={
            "incident_type": "other",
            "description": "Caso AC-05",
            "event_date": "2026-04-14",
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert incident.status_code == 201, incident.text

    run_resp = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert run_resp.status_code == 200, run_resp.text

    detail = await client.get(
        f"/alerts/students/{student.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["traffic_light"] == "red"
    alert_id = detail.json()["active_alerts"][0]["id"]

    resolved = await client.post(
        f"/alerts/resolve/{alert_id}",
        json={"coordinator_note": "Resuelto en AC-05"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert resolved.status_code == 200
    assert resolved.json()["is_active"] is False


@pytest.mark.asyncio
async def test_ac06_student_cannot_access_other_student_logbook_entry(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_logbook_entry,
    auth_headers,
):
    """AC-06: Privacidad, estudiante no puede leer bitacora de otro estudiante."""
    student_a = await create_user("student", full_name="Alumno A")
    student_b = await create_user("student", full_name="Alumno B")
    cohort = await create_cohort()

    entry = await create_logbook_entry(
        student_id=student_a.id,
        cohort_id=cohort.id,
        week_number=3,
    )

    resp = await client.get(
        f"/logbook/entries/{entry.id}",
        headers=auth_headers(str(student_b.id), "student"),
    )
    assert resp.status_code == 403
