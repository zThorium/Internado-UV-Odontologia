from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_logbook_my_context_returns_assignment_based_defaults(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    student = await create_user("student")
    tutor = await create_user("tutor")
    cohort = await create_cohort(name="Cohorte Context")

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
        care_level="primary",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 6, 30),
    )

    resp = await client.get(
        "/logbook/my-context",
        headers=auth_headers(str(student.id), "student"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["cohort_id"] == str(cohort.id)
    assert data["care_level"] == "primary"
    assert isinstance(data["allowed_procedures"], list)
    assert len(data["allowed_procedures"]) > 0


@pytest.mark.asyncio
async def test_logbook_delete_entry_rules(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_logbook_entry,
    auth_headers,
):
    student = await create_user("student")
    cohort = await create_cohort(name="Cohorte Delete")

    draft_entry = await create_logbook_entry(
        student_id=student.id,
        cohort_id=cohort.id,
        week_number=10,
        status="draft",
    )

    delete_draft = await client.delete(
        f"/logbook/entries/{draft_entry.id}",
        headers=auth_headers(str(student.id), "student"),
    )
    assert delete_draft.status_code == 204, delete_draft.text

    reviewed_entry = await create_logbook_entry(
        student_id=student.id,
        cohort_id=cohort.id,
        week_number=11,
        status="reviewed",
    )

    delete_reviewed = await client.delete(
        f"/logbook/entries/{reviewed_entry.id}",
        headers=auth_headers(str(student.id), "student"),
    )
    assert delete_reviewed.status_code == 422
