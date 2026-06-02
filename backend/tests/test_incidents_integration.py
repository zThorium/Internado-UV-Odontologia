"""
Tests de integración para el módulo de incidentes (/incidents).

Flujos cubiertos:
1. Estudiante crea incidente → 201, status="submitted"
2. Estudiante lista sus incidentes → solo ve los propios
3. Coordinador lista todos los incidentes → ve los de todos los estudiantes
4. Tutor no puede usar endpoint de estudiante para crear incidente → 403
5. Tutor crea incidente para estudiante asignado → 201
6. Tutor lista solo incidentes levantados por él
7. Coordinador cambia status a "under_review" → 200
8. Coordinador cambia status a "resolved" → 200
9. Fallo de email no impide creación del incidente → 201 igual
"""
import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.core.security import create_access_token
from app.models.assignment import Assignment
from app.models.cohort import Cohort
from app.models.user import User


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _token(user_id: str, role: str) -> str:
    return create_access_token({"sub": user_id, "role": role})


def _auth(user_id: str, role: str) -> dict:
    return {"Authorization": f"Bearer {_token(user_id, role)}"}


def _incident_payload(incident_type: str = "abuse") -> dict:
    return {
        "incident_type": incident_type,
        "description": "Descripción del incidente de prueba",
        "event_date": str(date(2024, 3, 15)),
    }


async def _create_user(db: AsyncSession, user_id: str, role: str, full_name: str) -> None:
    db.add(
        User(
            id=uuid.UUID(user_id),
            email=f"{user_id}@test.local",
            hashed_password="hashed",
            full_name=full_name,
            role=role,
            is_active=True,
        )
    )
    await db.commit()


async def _create_assignment(db: AsyncSession, student_id: str, tutor_id: str) -> None:
    cohort = Cohort(
        id=uuid.uuid4(),
        name="Cohorte Incidentes",
        year=2026,
        semester=1,
        is_active=True,
    )
    db.add(cohort)
    await db.flush()

    db.add(
        Assignment(
            id=uuid.uuid4(),
            student_id=uuid.UUID(student_id),
            tutor_id=uuid.UUID(tutor_id),
            cohort_id=cohort.id,
            care_level="primary",
            clinical_site="CESFAM Prueba",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
            is_active=True,
        )
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Test 1: Estudiante crea incidente → 201, status="submitted"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_creates_incident(client: AsyncClient):
    student_id = str(uuid.uuid4())

    resp = await client.post(
        "/incidents",
        json=_incident_payload("harassment"),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "submitted"
    assert data["incident_type"] == "harassment"
    assert data["student_id"] == student_id


# ---------------------------------------------------------------------------
# Test 2: Estudiante lista sus incidentes → solo ve los propios
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_lists_only_own_incidents(client: AsyncClient):
    student_a = str(uuid.uuid4())
    student_b = str(uuid.uuid4())

    # student_a crea un incidente
    resp = await client.post(
        "/incidents",
        json=_incident_payload("abuse"),
        headers=_auth(student_a, "student"),
    )
    assert resp.status_code == 201

    # student_b crea un incidente
    resp = await client.post(
        "/incidents",
        json=_incident_payload("other"),
        headers=_auth(student_b, "student"),
    )
    assert resp.status_code == 201

    # student_a lista → solo ve el suyo
    resp = await client.get("/incidents", headers=_auth(student_a, "student"))
    assert resp.status_code == 200
    incidents = resp.json()
    assert len(incidents) == 1
    assert incidents[0]["student_id"] == student_a


# ---------------------------------------------------------------------------
# Test 3: Coordinador lista todos los incidentes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_lists_all_incidents(client: AsyncClient, db_session: AsyncSession):
    student_a = str(uuid.uuid4())
    student_b = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())

    await _create_user(db_session, student_a, "student", "Estudiante A")
    await _create_user(db_session, student_b, "student", "Estudiante B")

    # Dos estudiantes crean incidentes
    for student_id in (student_a, student_b):
        resp = await client.post(
            "/incidents",
            json=_incident_payload("discrimination"),
            headers=_auth(student_id, "student"),
        )
        assert resp.status_code == 201

    # Coordinador lista todos
    resp = await client.get("/incidents", headers=_auth(coordinator_id, "coordinator"))
    assert resp.status_code == 200
    incidents = resp.json()
    assert len(incidents) == 2
    student_ids = {i["student_id"] for i in incidents}
    assert student_a in student_ids
    assert student_b in student_ids


# ---------------------------------------------------------------------------
# Test 4: Tutor no puede usar endpoint de estudiante para crear incidente → 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_cannot_create_incident(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    resp = await client.post(
        "/incidents",
        json=_incident_payload("abuse"),
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Test 5: Tutor crea incidente para estudiante asignado
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_creates_incident_for_assigned_student(client: AsyncClient, db_session: AsyncSession):
    tutor_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    await _create_user(db_session, tutor_id, "tutor", "Tutor Incidente")
    await _create_user(db_session, student_id, "student", "Estudiante Incidente")
    await _create_assignment(db_session, student_id, tutor_id)

    resp = await client.post(
        "/incidents/tutor",
        json={
            "student_id": student_id,
            "title": "Ausencias reiteradas",
            "description": "Presenta ausencias no justificadas en 2 semanas consecutivas",
            "event_date": "2026-04-10",
            "urgency_level": "high",
        },
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["reporter_role"] == "tutor"
    assert payload["urgency_level"] == "high"
    assert payload["title"] == "Ausencias reiteradas"


# ---------------------------------------------------------------------------
# Test 6: Tutor lista solo sus incidentes levantados
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_lists_only_own_reported_incidents(client: AsyncClient, db_session: AsyncSession):
    tutor_a = str(uuid.uuid4())
    tutor_b = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    await _create_user(db_session, tutor_a, "tutor", "Tutor A")
    await _create_user(db_session, tutor_b, "tutor", "Tutor B")
    await _create_user(db_session, student_id, "student", "Estudiante Compartido")
    await _create_assignment(db_session, student_id, tutor_a)
    await _create_assignment(db_session, student_id, tutor_b)

    for tutor_id, title in ((tutor_a, "Incidente A"), (tutor_b, "Incidente B")):
        resp = await client.post(
            "/incidents/tutor",
            json={
                "student_id": student_id,
                "title": title,
                "description": "Detalle",
                "event_date": "2026-04-10",
                "urgency_level": "medium",
            },
            headers=_auth(tutor_id, "tutor"),
        )
        assert resp.status_code == 201, resp.text

    list_resp = await client.get("/incidents", headers=_auth(tutor_a, "tutor"))
    assert list_resp.status_code == 200, list_resp.text
    data = list_resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Incidente A"


# ---------------------------------------------------------------------------
# Test 6: Coordinador cambia status a "under_review" → 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_changes_status_to_under_review(client: AsyncClient):
    student_id = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())

    resp = await client.post(
        "/incidents",
        json=_incident_payload("abuse"),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201
    incident_id = resp.json()["id"]

    resp = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "under_review"},
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "under_review"


# ---------------------------------------------------------------------------
# Test 7: Coordinador cambia status a "resolved" → 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_changes_status_to_resolved(client: AsyncClient):
    student_id = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())

    resp = await client.post(
        "/incidents",
        json=_incident_payload("other"),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201
    incident_id = resp.json()["id"]

    # Primero under_review
    await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "under_review"},
        headers=_auth(coordinator_id, "coordinator"),
    )

    # Luego resolved
    resp = await client.patch(
        f"/incidents/{incident_id}/status",
        json={"status": "resolved"},
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "resolved"


# ---------------------------------------------------------------------------
# Test 8: Fallo de email no impide creación del incidente
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_email_failure_does_not_prevent_incident_creation(client: AsyncClient):
    student_id = str(uuid.uuid4())

    with patch(
        "app.services.incidents.send_incident_notification",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP connection failed"),
    ):
        resp = await client.post(
            "/incidents",
            json=_incident_payload("harassment"),
            headers=_auth(student_id, "student"),
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "submitted"
    assert data["student_id"] == student_id


# ---------------------------------------------------------------------------
# Test 9: Estudiante puede ver su propio incidente por ID
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_gets_own_incident_by_id(client: AsyncClient):
    student_id = str(uuid.uuid4())

    created = await client.post(
        "/incidents",
        json=_incident_payload("abuse"),
        headers=_auth(student_id, "student"),
    )
    assert created.status_code == 201
    incident_id = created.json()["id"]

    resp = await client.get(
        f"/incidents/{incident_id}",
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == incident_id


# ---------------------------------------------------------------------------
# Test 10: Estudiante no puede ver incidente de otro estudiante
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_cannot_get_other_student_incident(client: AsyncClient):
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())

    created = await client.post(
        "/incidents",
        json=_incident_payload("other"),
        headers=_auth(owner_id, "student"),
    )
    assert created.status_code == 201
    incident_id = created.json()["id"]

    forbidden = await client.get(
        f"/incidents/{incident_id}",
        headers=_auth(other_id, "student"),
    )
    assert forbidden.status_code == 403


# ---------------------------------------------------------------------------
# Test 11: Coordinador agrega respuesta al incidente
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_adds_response_to_incident(client: AsyncClient):
    student_id = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())

    created = await client.post(
        "/incidents",
        json=_incident_payload("harassment"),
        headers=_auth(student_id, "student"),
    )
    assert created.status_code == 201
    incident_id = created.json()["id"]

    resp = await client.patch(
        f"/incidents/{incident_id}/response",
        json={"coordinator_response": "Caso revisado y derivado"},
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["coordinator_response"] == "Caso revisado y derivado"


# ---------------------------------------------------------------------------
# Test 12: Tutor no asignado no puede crear incidente para estudiante
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_cannot_create_incident_for_unassigned_student(
    client: AsyncClient,
    db_session: AsyncSession,
):
    tutor_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    await _create_user(db_session, tutor_id, "tutor", "Tutor Sin Asignacion")
    await _create_user(db_session, student_id, "student", "Estudiante Sin Asignacion")

    resp = await client.post(
        "/incidents/tutor",
        json={
            "student_id": student_id,
            "title": "Sin asignacion",
            "description": "Intento no permitido",
            "event_date": "2026-04-12",
            "urgency_level": "medium",
        },
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Test 13: Payload inválido en incidente de estudiante retorna 422
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_create_incident_invalid_payload_returns_422(client: AsyncClient):
    student_id = str(uuid.uuid4())

    resp = await client.post(
        "/incidents",
        json={
            "incident_type": "invalid_type",
            "description": "Payload inválido",
            "event_date": "2026-04-12",
        },
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test 14: Cambiar estado de incidente inexistente retorna 404
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_changes_status_of_missing_incident_returns_404(client: AsyncClient):
    coordinator_id = str(uuid.uuid4())
    missing_id = str(uuid.uuid4())

    resp = await client.patch(
        f"/incidents/{missing_id}/status",
        json={"status": "under_review"},
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test 15: Falla de notificación en incidente de tutor no bloquea creación
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_incident_email_failure_does_not_prevent_creation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    tutor_id = str(uuid.uuid4())
    student_id = str(uuid.uuid4())

    await _create_user(db_session, tutor_id, "tutor", "Tutor Resiliente")
    await _create_user(db_session, student_id, "student", "Estudiante Resiliente")
    await _create_assignment(db_session, student_id, tutor_id)

    with patch(
        "app.services.incidents.send_incident_notification",
        new_callable=AsyncMock,
        side_effect=Exception("smtp-down"),
    ):
        resp = await client.post(
            "/incidents/tutor",
            json={
                "student_id": student_id,
                "title": "Seguimiento crítico",
                "description": "Se mantiene creación pese a error de email",
                "event_date": "2026-04-12",
                "urgency_level": "high",
            },
            headers=_auth(tutor_id, "tutor"),
        )

    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload["reporter_role"] == "tutor"
    assert payload["student_id"] == student_id
