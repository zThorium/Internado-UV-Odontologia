from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_dashboard_assignment_lifecycle_and_overview(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coord Dashboard")
    tutor = await create_user("tutor", full_name="Tutor Dashboard")
    student = await create_user("student", full_name="Estudiante Dashboard")

    cohort_resp = await client.post(
        "/dashboard/cohorts",
        json={"year": 2026, "semester": 1, "name": "Cohorte 2026-1"},
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
            "clinical_site": "Hospital Dental",
            "start_date": str(date(2026, 1, 1)),
            "end_date": str(date(2026, 6, 30)),
        },
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert assignment_resp.status_code == 201, assignment_resp.text
    assignment = assignment_resp.json()
    assert assignment["student_id"] == str(student.id)
    assert assignment["tutor_id"] == str(tutor.id)
    assert assignment["is_active"] is True

    list_resp = await client.get(
        "/dashboard/assignments",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert list_resp.status_code == 200, list_resp.text
    assignments = list_resp.json()
    assert len(assignments) == 1
    assert assignments[0]["student_name"] == "Estudiante Dashboard"
    assert assignments[0]["tutor_name"] == "Tutor Dashboard"

    overview_resp = await client.get(
        "/dashboard/overview",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert overview_resp.status_code == 200, overview_resp.text
    overview = overview_resp.json()
    assert overview["total_students"] >= 1
    assert overview["total_tutors"] >= 1

    deactivate_resp = await client.patch(
        f"/dashboard/assignments/{assignment['id']}/deactivate",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert deactivate_resp.status_code == 200, deactivate_resp.text
    assert deactivate_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_dashboard_cannot_create_duplicate_cohort_same_year_semester(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    coordinator = await create_user("coordinator")
    payload = {"year": 2026, "semester": 2, "name": "Cohorte Unica"}

    first = await client.post(
        "/dashboard/cohorts",
        json=payload,
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/dashboard/cohorts",
        json=payload,
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert second.status_code == 409, second.text


@pytest.mark.asyncio
async def test_dashboard_students_endpoint_filters_by_query(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    coordinator = await create_user("coordinator")
    await create_user("student", full_name="Ana Perez", email="ana@test.local")
    await create_user("student", full_name="Juan Soto", email="juan@test.local")
    await create_user("tutor", full_name="Tutor Fuera", email="tutor@test.local")

    resp = await client.get(
        "/dashboard/students?q=ana",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    students = resp.json()
    assert len(students) == 1
    assert students[0]["full_name"] == "Ana Perez"
