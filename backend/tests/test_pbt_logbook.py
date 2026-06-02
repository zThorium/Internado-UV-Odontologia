"""
Tests de propiedad (Property-Based Testing) con Hypothesis para privacidad de bitácora.

Valida: Requirements 3.3, 3.4

Propiedades verificadas:
- P1: Para cualquier student_id distinto al del token JWT del estudiante autenticado,
      GET /logbook/entries/{entry_id} retorna 403
- P2: Para cualquier student_id distinto al del token JWT del estudiante autenticado,
      PUT /logbook/entries/{entry_id} retorna 403
"""
import asyncio
import uuid
from datetime import date

import pytest
from httpx import AsyncClient, ASGITransport
from hypothesis import given, settings, strategies as st
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.core.security import create_access_token


pytestmark = [pytest.mark.integration, pytest.mark.property]


# ---------------------------------------------------------------------------
# Fixtures: base de datos SQLite en memoria compartida para los PBT
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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
# Helper síncrono para Hypothesis (no soporta async nativamente)
# ---------------------------------------------------------------------------

def _run_async(coro):
    """Ejecuta una coroutine en un event loop nuevo."""
    return asyncio.run(coro)


async def _setup_db_and_entry(owner_id: str) -> tuple[str, object, object]:
    """
    Crea una DB en memoria, inserta una entrada de bitácora para owner_id,
    y retorna (entry_id, engine, session_factory).
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    cohort_id = uuid.uuid4()
    entry_id = None

    async with session_factory() as session:

        async def override_get_db():
            yield session

        fastapi_app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as ac:
            resp = await ac.post(
                "/logbook/entries",
                json=_entry_payload(cohort_id, week=1),
                headers=_auth(owner_id, "student"),
            )
            assert resp.status_code == 201, f"Setup falló: {resp.text}"
            entry_id = resp.json()["id"]

        fastapi_app.dependency_overrides.clear()

    return entry_id, engine, session_factory


async def _check_get_entry_returns_403(entry_id: str, requester_id: str, engine, session_factory) -> int:
    """GET /logbook/entries/{entry_id} con token de requester_id → retorna status code."""
    async with session_factory() as session:

        async def override_get_db():
            yield session

        fastapi_app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                f"/logbook/entries/{entry_id}",
                headers=_auth(requester_id, "student"),
            )
            status_code = resp.status_code

        fastapi_app.dependency_overrides.clear()

    await engine.dispose()
    return status_code


async def _check_put_entry_returns_403(entry_id: str, requester_id: str, engine, session_factory) -> int:
    """PUT /logbook/entries/{entry_id} con token de requester_id → retorna status code."""
    async with session_factory() as session:

        async def override_get_db():
            yield session

        fastapi_app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=fastapi_app), base_url="http://test"
        ) as ac:
            resp = await ac.put(
                f"/logbook/entries/{entry_id}",
                json={"procedures": [{"name": "Otro", "description": "", "quantity": 1}]},
                headers=_auth(requester_id, "student"),
            )
            status_code = resp.status_code

        fastapi_app.dependency_overrides.clear()

    await engine.dispose()
    return status_code


# ---------------------------------------------------------------------------
# P1: GET /logbook/entries/{entry_id} con token de otro estudiante → 403
# Validates: Requirements 3.3, 3.4
# ---------------------------------------------------------------------------

@given(
    owner_id=st.uuids().map(str),
    requester_id=st.uuids().map(str),
)
@settings(max_examples=20)
def test_p1_get_entry_by_non_owner_student_returns_403(owner_id: str, requester_id: str):
    """
    **Validates: Requirements 3.3, 3.4**

    P1: Para cualquier par (owner_id, requester_id) donde owner_id != requester_id,
    GET /logbook/entries/{entry_id} con token del requester retorna 403.
    """
    # Hypothesis puede generar el mismo UUID para ambos; en ese caso el test no aplica
    if owner_id == requester_id:
        return

    async def _run():
        entry_id, engine, session_factory = await _setup_db_and_entry(owner_id)
        return await _check_get_entry_returns_403(entry_id, requester_id, engine, session_factory)

    status_code = _run_async(_run())
    assert status_code == 403, (
        f"Esperado 403 pero obtuvo {status_code} "
        f"(owner={owner_id}, requester={requester_id})"
    )


# ---------------------------------------------------------------------------
# P2: PUT /logbook/entries/{entry_id} con token de otro estudiante → 403
# Validates: Requirements 3.3, 3.4
# ---------------------------------------------------------------------------

@given(
    owner_id=st.uuids().map(str),
    requester_id=st.uuids().map(str),
)
@settings(max_examples=20)
def test_p2_put_entry_by_non_owner_student_returns_403(owner_id: str, requester_id: str):
    """
    **Validates: Requirements 3.3, 3.4**

    P2: Para cualquier par (owner_id, requester_id) donde owner_id != requester_id,
    PUT /logbook/entries/{entry_id} con token del requester retorna 403.
    """
    if owner_id == requester_id:
        return

    async def _run():
        entry_id, engine, session_factory = await _setup_db_and_entry(owner_id)
        return await _check_put_entry_returns_403(entry_id, requester_id, engine, session_factory)

    status_code = _run_async(_run())
    assert status_code == 403, (
        f"Esperado 403 pero obtuvo {status_code} "
        f"(owner={owner_id}, requester={requester_id})"
    )
