"""
Tests de integración para el módulo de bitácora (/logbook).

Flujos cubiertos:
1. Flujo completo: estudiante crea → edita → coordinador cambia status a "reviewed"
   → estudiante intenta editar y recibe 409
2. Tutor sigue bloqueado para crear/editar/cambiar estado en /logbook
3. Estudiante intenta ver entradas de otro estudiante → recibe 403
4. Crear entrada duplicada para misma semana/cohorte → recibe 409
5. Coordinador puede ver entradas de cualquier estudiante
"""
import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.session import Base, get_db
from app.core.security import create_access_token


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixtures: base de datos SQLite en memoria
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Crea una base de datos SQLite en memoria para cada test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Importar todos los modelos para que Base los registre
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
    """AsyncClient con override de la dependencia get_db."""

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


def _entry_payload(cohort_id: uuid.UUID, week: int = 1) -> dict:
    return {
        "cohort_id": str(cohort_id),
        "week_number": week,
        "week_start_date": str(date(2024, 1, 1)),
        "wellbeing_status": "good",
        "procedures": [
            {"name": "Extracción", "description": "Molar inferior", "quantity": 2}
        ],
    }


# ---------------------------------------------------------------------------
# Flujo 1: crear → editar → coordinador cambia status → estudiante no puede editar
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_flow_create_edit_review_then_edit_blocked(client: AsyncClient):
    student_id = str(uuid.uuid4())
    cohort_id = uuid.uuid4()
    coordinator_id = str(uuid.uuid4())

    # 1. Estudiante crea entrada
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=1),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201, resp.text
    entry_id = resp.json()["id"]
    assert resp.json()["status"] == "draft"

    # 2. Estudiante edita la entrada (status=draft → permitido)
    resp = await client.put(
        f"/logbook/entries/{entry_id}",
        json={"procedures": [{"name": "Limpieza", "description": "", "quantity": 1}]},
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["procedures"][0]["name"] == "Limpieza"

    # 3. Coordinador cambia status a "reviewed"
    resp = await client.patch(
        f"/logbook/entries/{entry_id}/status",
        json={"status": "reviewed"},
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "reviewed"

    # 4. Estudiante intenta editar entrada ya revisada → 409
    resp = await client.put(
        f"/logbook/entries/{entry_id}",
        json={"procedures": [{"name": "Otro", "description": "", "quantity": 1}]},
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 409, resp.text


# ---------------------------------------------------------------------------
# Flujo 2: tutor bloqueado para crear/editar/cambiar estado en /logbook
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_blocked_from_list_entries(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    resp = await client.get(
        "/logbook/entries",
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_tutor_blocked_from_create_entry(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    cohort_id = uuid.uuid4()
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id),
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_tutor_blocked_from_get_entry(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    fake_entry_id = str(uuid.uuid4())
    resp = await client.get(
        f"/logbook/entries/{fake_entry_id}",
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tutor_blocked_from_update_entry(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    fake_entry_id = str(uuid.uuid4())
    resp = await client.put(
        f"/logbook/entries/{fake_entry_id}",
        json={"procedures": [{"name": "X", "description": "", "quantity": 1}]},
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_tutor_blocked_from_change_status(client: AsyncClient):
    tutor_id = str(uuid.uuid4())
    fake_entry_id = str(uuid.uuid4())
    resp = await client.patch(
        f"/logbook/entries/{fake_entry_id}/status",
        json={"status": "reviewed"},
        headers=_auth(tutor_id, "tutor"),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Flujo 3: estudiante intenta ver entradas de otro estudiante → 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_cannot_view_other_student_entries(client: AsyncClient):
    student_a = str(uuid.uuid4())
    student_b = str(uuid.uuid4())
    cohort_id = uuid.uuid4()

    # student_a crea una entrada
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=1),
        headers=_auth(student_a, "student"),
    )
    assert resp.status_code == 201
    entry_id = resp.json()["id"]

    # student_b intenta ver la entrada de student_a → 403
    resp = await client.get(
        f"/logbook/entries/{entry_id}",
        headers=_auth(student_b, "student"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_student_cannot_list_other_student_entries_via_student_endpoint(
    client: AsyncClient,
):
    """
    GET /logbook/entries usa current_user.id como student_id,
    por lo que student_b solo ve sus propias entradas (lista vacía), no las de student_a.
    """
    student_a = str(uuid.uuid4())
    student_b = str(uuid.uuid4())
    cohort_id = uuid.uuid4()

    # student_a crea una entrada
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=1),
        headers=_auth(student_a, "student"),
    )
    assert resp.status_code == 201

    # student_b lista sus propias entradas → lista vacía (no ve las de student_a)
    resp = await client.get(
        "/logbook/entries",
        headers=_auth(student_b, "student"),
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# Flujo 4: entrada duplicada para misma semana/cohorte → 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_entry_same_week_cohort_returns_409(client: AsyncClient):
    student_id = str(uuid.uuid4())
    cohort_id = uuid.uuid4()

    # Primera entrada → 201
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=3),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201

    # Segunda entrada misma semana/cohorte → 409
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=3),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_different_week_same_cohort_allowed(client: AsyncClient):
    """Semanas distintas en la misma cohorte no son duplicados."""
    student_id = str(uuid.uuid4())
    cohort_id = uuid.uuid4()

    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=1),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201

    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=2),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Flujo 5: coordinador puede ver entradas de cualquier estudiante
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_can_view_any_student_entry(client: AsyncClient):
    student_id = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())
    cohort_id = uuid.uuid4()

    # Estudiante crea entrada
    resp = await client.post(
        "/logbook/entries",
        json=_entry_payload(cohort_id, week=1),
        headers=_auth(student_id, "student"),
    )
    assert resp.status_code == 201
    entry_id = resp.json()["id"]

    # Coordinador puede ver esa entrada
    resp = await client.get(
        f"/logbook/entries/{entry_id}",
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == entry_id


@pytest.mark.asyncio
async def test_coordinator_can_list_any_student_entries(client: AsyncClient):
    student_id = str(uuid.uuid4())
    coordinator_id = str(uuid.uuid4())
    cohort_id = uuid.uuid4()

    # Estudiante crea dos entradas
    for week in (1, 2):
        resp = await client.post(
            "/logbook/entries",
            json=_entry_payload(cohort_id, week=week),
            headers=_auth(student_id, "student"),
        )
        assert resp.status_code == 201

    # Coordinador lista entradas del estudiante via endpoint dedicado
    resp = await client.get(
        f"/logbook/students/{student_id}/entries",
        headers=_auth(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 2
    assert entries[0]["week_number"] < entries[1]["week_number"]  # ordenadas ASC
