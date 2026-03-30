"""
Tests de integración para el módulo de incidentes (/incidents).

Flujos cubiertos:
1. Estudiante crea incidente → 201, status="submitted"
2. Estudiante lista sus incidentes → solo ve los propios
3. Coordinador lista todos los incidentes → ve los de todos los estudiantes
4. Tutor intenta crear incidente → 403
5. Tutor intenta listar incidentes → 403
6. Coordinador cambia status a "under_review" → 200
7. Coordinador cambia status a "resolved" → 200
8. Fallo de email no impide creación del incidente → 201 igual
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
async def test_coordinator_lists_all_incidents(client: AsyncClient):
    student_a = str(uuid.uuid4())
    student_b = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())

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
# Test 4: Tutor intenta crear incidente → 403
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
# Test 5: Tutor intenta listar incidentes → 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_cannot_list_incidents(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    resp = await client.get("/incidents", headers=_auth(tutor_id, "tutor"))
    assert resp.status_code == 403


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
