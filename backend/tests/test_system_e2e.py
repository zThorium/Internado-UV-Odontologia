from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.routers.auth as auth_router
import app.services.incidents as incidents_service
from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models.user import User


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


@pytest.mark.asyncio
async def test_end_to_end_role_boundaries_after_operational_flow(
    client: AsyncClient,
    create_user,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coordinador Seguridad E2E")
    tutor = await create_user("tutor", full_name="Tutor Seguridad E2E")
    student_a = await create_user("student", full_name="Estudiante A E2E")
    student_b = await create_user("student", full_name="Estudiante B E2E")

    cohort_resp = await client.post(
        "/dashboard/cohorts",
        json={"year": 2026, "semester": 2, "name": "Cohorte Seguridad"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert cohort_resp.status_code == 201, cohort_resp.text
    cohort_id = cohort_resp.json()["id"]

    assignment_resp = await client.post(
        "/dashboard/assignments",
        json={
            "student_id": str(student_a.id),
            "tutor_id": str(tutor.id),
            "cohort_id": cohort_id,
            "care_level": "secondary",
            "clinical_site": "Hospital de Seguridad",
            "start_date": str(date(2026, 7, 1)),
            "end_date": str(date(2026, 12, 31)),
        },
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert assignment_resp.status_code == 201, assignment_resp.text
    assignment_id = assignment_resp.json()["id"]

    eval_resp = await client.post(
        "/evaluations",
        json={
            "student_id": str(student_a.id),
            "assignment_id": assignment_id,
            "period_label": "Semana Seguridad",
            "overall_comment": "Evaluacion para validar privacidad",
            "items": [
                {"dimension": "Actitud", "score": 4, "comment": "Adecuada"},
                {"dimension": "Tecnica", "score": 4, "comment": "Adecuada"},
            ],
        },
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert eval_resp.status_code == 201, eval_resp.text

    tutor_students_resp = await client.get(
        "/evaluations/my-students",
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert tutor_students_resp.status_code == 200, tutor_students_resp.text
    tutor_students = tutor_students_resp.json()
    assert any(student["id"] == str(student_a.id) for student in tutor_students)
    assert all(student["id"] != str(student_b.id) for student in tutor_students)

    forbidden_eval_resp = await client.get(
        f"/evaluations/students/{student_a.id}",
        headers=auth_headers(str(student_b.id), "student"),
    )
    assert forbidden_eval_resp.status_code == 403, forbidden_eval_resp.text

    own_eval_resp = await client.get(
        f"/evaluations/students/{student_a.id}",
        headers=auth_headers(str(student_a.id), "student"),
    )
    assert own_eval_resp.status_code == 200, own_eval_resp.text
    assert len(own_eval_resp.json()) == 1

    forbidden_alerts_resp = await client.post(
        "/alerts/run",
        headers=auth_headers(str(student_a.id), "student"),
    )
    assert forbidden_alerts_resp.status_code == 403, forbidden_alerts_resp.text


@pytest.mark.asyncio
async def test_end_to_end_alert_lifecycle_after_tutor_validation(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    create_logbook_entry,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coordinador Alertas E2E")
    tutor = await create_user("tutor", full_name="Tutor Alertas E2E")
    student = await create_user("student", full_name="Estudiante Alertas E2E")
    cohort = await create_cohort(name="Cohorte Alerta Tutor E2E")

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    delayed_entry = await create_logbook_entry(
        student_id=student.id,
        cohort_id=cohort.id,
        week_number=8,
        week_start_date=date.today() - timedelta(days=28),
        status="submitted",
    )

    run_before = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert run_before.status_code == 200, run_before.text

    detail_before = await client.get(
        f"/alerts/students/{student.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert detail_before.status_code == 200, detail_before.text
    active_types_before = {alert["alert_type"] for alert in detail_before.json()["active_alerts"]}
    assert "no_tutor_validation" in active_types_before

    validate_resp = await client.post(
        f"/logbook/entries/{delayed_entry.id}/validate",
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert validate_resp.status_code == 200, validate_resp.text

    run_after = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert run_after.status_code == 200, run_after.text

    detail_after = await client.get(
        f"/alerts/students/{student.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert detail_after.status_code == 200, detail_after.text
    active_types_after = {alert["alert_type"] for alert in detail_after.json()["active_alerts"]}
    assert "no_tutor_validation" not in active_types_after


@pytest.mark.asyncio
async def test_end_to_end_authentication_degradation_and_recovery(
    client: AsyncClient,
    create_user,
    monkeypatch: pytest.MonkeyPatch,
):
    user = await create_user(
        "student",
        email="degradacion.auth@internado.cl",
        full_name="Estudiante Degradacion",
    )

    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", False)
    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: False)
    monkeypatch.setattr(auth_router, "verify_password", lambda plain, _: plain == "LocalPass123")

    degraded_login = await client.post(
        "/auth/login",
        json={"email": user.email, "password": "LocalPass123"},
    )
    assert degraded_login.status_code == 200, degraded_login.text
    degraded_payload = degraded_login.json()

    local_claims = decode_access_token(degraded_payload["access_token"])
    assert local_claims["auth_provider"] == "local"
    assert local_claims["sub"] == str(user.id)

    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: True)
    monkeypatch.setattr(
        auth_router,
        "login_with_password",
        lambda _, __: {
            "access_token": "oidc-access",
            "refresh_token": "oidc-refresh",
            "expires_in": 300,
            "token_type": "bearer",
        },
    )

    recovered_login = await client.post(
        "/auth/login",
        json={"email": user.email, "password": "OidcPass123"},
    )
    assert recovered_login.status_code == 200, recovered_login.text
    recovered_payload = recovered_login.json()
    assert recovered_payload["access_token"] == "oidc-access"
    assert recovered_payload["refresh_token"] == "oidc-refresh"


@pytest.mark.asyncio
async def test_end_to_end_sensitive_idempotency_for_alert_generation(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
):
    coordinator = await create_user("coordinator", full_name="Coordinador Idempotencia")
    tutor = await create_user("tutor", full_name="Tutor Idempotencia")
    student = await create_user("student", full_name="Estudiante Idempotencia")
    cohort = await create_cohort(name="Cohorte Idempotencia Sistema")

    await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
        start_date=date.today() - timedelta(weeks=10),
        end_date=date.today() + timedelta(weeks=10),
    )

    first_run = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert first_run.status_code == 200, first_run.text

    first_summary = await client.get(
        "/alerts/summary",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert first_summary.status_code == 200, first_summary.text

    second_run = await client.post(
        "/alerts/run",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert second_run.status_code == 200, second_run.text

    second_summary = await client.get(
        "/alerts/summary",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert second_summary.status_code == 200, second_summary.text
    assert second_summary.json() == first_summary.json()

    detail_resp = await client.get(
        f"/alerts/students/{student.id}",
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert detail_resp.status_code == 200, detail_resp.text
    active_types = [alert["alert_type"] for alert in detail_resp.json()["active_alerts"]]
    assert len(active_types) == len(set(active_types))
    assert len(active_types) >= 1


@pytest.mark.asyncio
async def test_end_to_end_concurrent_attendance_registration_conflict_handling(
    auth_headers,
    tmp_path,
):
    db_path = tmp_path / "attendance_concurrency_system.sqlite3"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    student_id = uuid.uuid4()
    try:
        async with session_factory() as seed_session:
            seed_session.add(
                User(
                    id=student_id,
                    email="concurrencia.e2e@internado.cl",
                    hashed_password="hashed",
                    full_name="Estudiante Concurrencia",
                    role="student",
                    is_active=True,
                )
            )
            await seed_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://test",
        ) as isolated_client:
            payload = {
                "date": "2026-05-12",
                "status": "present",
                "observation": "Registro simultaneo de asistencia",
            }

            responses = await asyncio.gather(
                *[
                    isolated_client.post(
                        "/attendance",
                        json=payload,
                        headers=auth_headers(str(student_id), "student"),
                    )
                    for _ in range(5)
                ]
            )

            status_codes = [response.status_code for response in responses]
            assert status_codes.count(201) == 1
            assert status_codes.count(409) == 4

            attendance_list = await isolated_client.get(
                "/attendance/me",
                headers=auth_headers(str(student_id), "student"),
            )
            assert attendance_list.status_code == 200, attendance_list.text
            same_day_entries = [entry for entry in attendance_list.json() if entry["date"] == "2026-05-12"]
            assert len(same_day_entries) == 1
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.mark.asyncio
async def test_end_to_end_flow_recovers_after_partial_incident_notification_error(
    client: AsyncClient,
    create_user,
    create_cohort,
    create_assignment,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    coordinator = await create_user("coordinator", full_name="Coordinador Resiliencia")
    tutor = await create_user("tutor", full_name="Tutor Resiliencia")
    student = await create_user("student", full_name="Estudiante Resiliencia")
    cohort = await create_cohort(name="Cohorte Resiliencia Sistema")

    assignment = await create_assignment(
        student_id=student.id,
        tutor_id=tutor.id,
        cohort_id=cohort.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
    )

    async def _failing_notification(*_args, **_kwargs):
        raise RuntimeError("smtp-down")

    monkeypatch.setattr(incidents_service, "send_incident_notification", _failing_notification)

    incident_resp = await client.post(
        "/incidents",
        json={
            "incident_type": "other",
            "description": "Incidente con notificacion fallida",
            "event_date": "2026-05-12",
        },
        headers=auth_headers(str(student.id), "student"),
    )
    assert incident_resp.status_code == 201, incident_resp.text
    incident_id = incident_resp.json()["id"]

    review_resp = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "under_review"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert review_resp.status_code == 200, review_resp.text

    resolved_resp = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "resolved"},
        headers=auth_headers(str(coordinator.id), "coordinator"),
    )
    assert resolved_resp.status_code == 200, resolved_resp.text

    attendance_resp = await client.post(
        "/attendance",
        json={"date": "2026-05-12", "status": "present", "observation": "Asistencia posterior"},
        headers=auth_headers(str(student.id), "student"),
    )
    assert attendance_resp.status_code == 201, attendance_resp.text

    evaluation_resp = await client.post(
        "/evaluations",
        json={
            "student_id": str(student.id),
            "assignment_id": str(assignment.id),
            "period_label": "Semana Resiliencia",
            "overall_comment": "Flujo completo tras error parcial",
            "items": [
                {"dimension": "Actitud", "score": 4, "comment": "Buena respuesta"},
                {"dimension": "Tecnica", "score": 4, "comment": "Buena respuesta"},
            ],
        },
        headers=auth_headers(str(tutor.id), "tutor"),
    )
    assert evaluation_resp.status_code == 201, evaluation_resp.text
