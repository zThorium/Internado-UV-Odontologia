from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_tutor_can_list_and_validate_assigned_student_logbook_entries(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    create_logbook_entry,
    auth_headers,
):
    tutor = await create_user('tutor', full_name='Tutor Validador')
    student = await create_user('student', full_name='Estudiante Bitacora')
    cohort = await create_cohort(name='Cohorte Tutor Logbook')

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
    )

    entry = await create_logbook_entry(
        student_id=student.id,
        cohort_id=cohort.id,
        week_number=8,
        status='submitted',
    )

    list_resp = await client.get(
        f'/logbook/tutor/students/{student.id}/entries',
        headers=auth_headers(str(tutor.id), 'tutor'),
    )
    assert list_resp.status_code == 200, list_resp.text
    rows = list_resp.json()
    assert len(rows) == 1
    assert rows[0]['tutor_validation'] is None

    validate_resp = await client.post(
        f'/logbook/entries/{entry.id}/validate',
        headers=auth_headers(str(tutor.id), 'tutor'),
    )
    assert validate_resp.status_code == 200, validate_resp.text
    payload = validate_resp.json()
    assert payload['tutor_validation'] is not None
    assert payload['tutor_validation']['tutor_id'] == str(tutor.id)


@pytest.mark.asyncio
async def test_tutor_cannot_validate_unassigned_student_logbook_entry(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_logbook_entry,
    auth_headers,
):
    tutor = await create_user('tutor', full_name='Tutor No Asignado')
    student = await create_user('student', full_name='Estudiante Ajeno')
    cohort = await create_cohort(name='Cohorte Ajena')

    entry = await create_logbook_entry(
        student_id=student.id,
        cohort_id=cohort.id,
        week_number=6,
        status='submitted',
    )

    resp = await client.post(
        f'/logbook/entries/{entry.id}/validate',
        headers=auth_headers(str(tutor.id), 'tutor'),
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_alert_no_tutor_validation_is_triggered_and_cleared_after_validation(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    create_logbook_entry,
    auth_headers,
):
    coordinator = await create_user('coordinator', full_name='Coord Alertas')
    tutor = await create_user('tutor', full_name='Tutor Alerta')
    student = await create_user('student', full_name='Estudiante Alerta')
    cohort = await create_cohort(name='Cohorte Alertas Tutor')

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
    )

    old_week_start = date.today() - timedelta(days=28)
    entry = await create_logbook_entry(
        student_id=student.id,
        cohort_id=cohort.id,
        week_number=4,
        week_start_date=old_week_start,
        status='submitted',
    )

    run_before = await client.post(
        '/alerts/run',
        headers=auth_headers(str(coordinator.id), 'coordinator'),
    )
    assert run_before.status_code == 200, run_before.text

    detail_before = await client.get(
        f'/alerts/students/{student.id}',
        headers=auth_headers(str(coordinator.id), 'coordinator'),
    )
    assert detail_before.status_code == 200, detail_before.text
    active_types = {alert['alert_type'] for alert in detail_before.json()['active_alerts']}
    assert 'no_tutor_validation' in active_types

    validate_resp = await client.post(
        f'/logbook/entries/{entry.id}/validate',
        headers=auth_headers(str(tutor.id), 'tutor'),
    )
    assert validate_resp.status_code == 200, validate_resp.text

    run_after = await client.post(
        '/alerts/run',
        headers=auth_headers(str(coordinator.id), 'coordinator'),
    )
    assert run_after.status_code == 200, run_after.text

    detail_after = await client.get(
        f'/alerts/students/{student.id}',
        headers=auth_headers(str(coordinator.id), 'coordinator'),
    )
    assert detail_after.status_code == 200, detail_after.text
    active_types_after = {alert['alert_type'] for alert in detail_after.json()['active_alerts']}
    assert 'no_tutor_validation' not in active_types_after
