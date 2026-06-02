from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_student_registers_and_lists_own_attendance(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    student = await create_user("student", full_name="Estudiante Asistencia")

    payload = {
        "date": str(date(2026, 4, 1)),
        "status": "present",
        "observation": "Ingreso puntual",
    }

    create_resp = await client.post(
        "/attendance",
        json=payload,
        headers=auth_headers(str(student.id), "student"),
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["student_id"] == str(student.id)
    assert created["status"] == "present"

    list_resp = await client.get(
        "/attendance/me",
        headers=auth_headers(str(student.id), "student"),
    )
    assert list_resp.status_code == 200, list_resp.text
    entries = list_resp.json()
    assert len(entries) == 1
    assert entries[0]["date"] == "2026-04-01"


@pytest.mark.asyncio
async def test_student_cannot_create_duplicate_attendance_for_same_day(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    student = await create_user("student")
    payload = {"date": "2026-04-02", "status": "present", "observation": None}

    first = await client.post(
        "/attendance",
        json=payload,
        headers=auth_headers(str(student.id), "student"),
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/attendance",
        json=payload,
        headers=auth_headers(str(student.id), "student"),
    )
    assert second.status_code == 409, second.text
    assert "Ya existe" in second.json()["detail"]


@pytest.mark.asyncio
async def test_student_updates_own_record_and_cannot_update_others(
    client: AsyncClient,
    create_user,
    create_attendance_record,
    auth_headers,
):
    owner = await create_user("student", full_name="Owner")
    outsider = await create_user("student", full_name="Outsider")

    record = await create_attendance_record(
        student_id=owner.id,
        attendance_date=date(2026, 4, 3),
        status="present",
    )

    forbidden = await client.patch(
        f"/attendance/{record.id}",
        json={"status": "absent", "observation": "No corresponde"},
        headers=auth_headers(str(outsider.id), "student"),
    )
    assert forbidden.status_code == 403, forbidden.text

    update_resp = await client.patch(
        f"/attendance/{record.id}",
        json={"status": "justified", "observation": "Licencia médica"},
        headers=auth_headers(str(owner.id), "student"),
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["status"] == "justified"
    assert updated["observation"] == "Licencia médica"


@pytest.mark.asyncio
async def test_tutor_can_view_assigned_student_attendance_and_stats(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    create_attendance_record,
    auth_headers,
):
    tutor = await create_user("tutor", full_name="Tutor Asignado")
    student = await create_user("student", full_name="Estudiante Asignado")
    cohort = await create_cohort()

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
    )

    await create_attendance_record(student.id, date(2026, 4, 1), "present")
    await create_attendance_record(student.id, date(2026, 4, 2), "absent")
    await create_attendance_record(student.id, date(2026, 4, 3), "present")

    records_resp = await client.get(
        f"/attendance/students/{student.id}",
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert records_resp.status_code == 200, records_resp.text
    records = records_resp.json()
    assert len(records) == 3
    assert records[0]["date"] == "2026-04-03"

    stats_resp = await client.get(
        f"/attendance/students/{student.id}/stats",
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert stats_resp.status_code == 200, stats_resp.text
    stats = stats_resp.json()
    assert stats["total"] == 3
    assert stats["present"] == 2
    assert stats["absent"] == 1
    assert stats["attendance_rate"] == 66.7


@pytest.mark.asyncio
async def test_tutor_cannot_view_unassigned_student_attendance(
    client: AsyncClient,
    create_user,
    create_attendance_record,
    auth_headers,
):
    tutor = await create_user("tutor")
    student = await create_user("student")
    await create_attendance_record(student.id, date(2026, 4, 10), "present")

    resp = await client.get(
        f"/attendance/students/{student.id}",
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert resp.status_code == 403, resp.text
