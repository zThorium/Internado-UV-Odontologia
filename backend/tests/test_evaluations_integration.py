"""
Tests de integración para el módulo de evaluaciones (/evaluations).

Flujos cubiertos:
1. Tutor lista sus estudiantes asignados → retorna lista correcta
2. Tutor evalúa estudiante asignado → 201
3. Tutor intenta evaluar estudiante NO asignado → 403
4. Estudiante ve sus propias evaluaciones → 200
5. Estudiante intenta ver evaluaciones de otro estudiante → 403
6. Coordinador puede ver evaluaciones de cualquier estudiante → 200
7. (PBT) Para cualquier student_id no asignado al tutor, POST /evaluations retorna 403
"""
import asyncio
import uuid
from datetime import date

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.main import app as fastapi_app
from app.db.session import Base, get_db
from app.core.security import create_access_token
from app.models.cohort import Cohort
from app.models.assignment import Assignment
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

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _token(user_id: str, role: str) -> str:
    return create_access_token({"sub": user_id, "role": role})


def _auth(user_id: str, role: str) -> dict:
    return {"Authorization": f"Bearer {_token(user_id, role)}"}


def _eval_payload(student_id: uuid.UUID, assignment_id: uuid.UUID) -> dict:
    return {
        "student_id": str(student_id),
        "assignment_id": str(assignment_id),
        "period_label": "Semana 1",
        "overall_comment": "Buen desempeño",
        "items": [
            {"dimension": "Actitud", "score": 5, "comment": "Excelente"},
            {"dimension": "Técnica", "score": 3, "comment": None},
        ],
    }


async def _create_assignment(
    db: AsyncSession,
    student_id: uuid.UUID,
    tutor_id: uuid.UUID,
    clinical_site: str = "Hospital Central",
    is_active: bool = True,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Crea Cohort + Assignment en la DB. Retorna (cohort_id, assignment_id)."""
    cohort = Cohort(
        id=uuid.uuid4(),
        name="Cohorte 2024",
        year=2024,
        semester=1,
        is_active=True,
    )
    db.add(cohort)
    await db.flush()

    assignment = Assignment(
        id=uuid.uuid4(),
        student_id=student_id,
        tutor_id=tutor_id,
        cohort_id=cohort.id,
        clinical_site=clinical_site,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        is_active=is_active,
    )
    db.add(assignment)
    await db.commit()

    return cohort.id, assignment.id


async def _create_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: str,
    full_name: str = "Test User",
) -> User:
    user = User(
        id=user_id,
        email=f"{user_id}@test.com",
        hashed_password="hashed",
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    return user


# ---------------------------------------------------------------------------
# Test 1: Tutor lista sus estudiantes asignados
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_lists_assigned_students(client: AsyncClient, db_session: AsyncSession):
    tutor_id = uuid.uuid4()
    student_id = uuid.uuid4()

    await _create_user(db_session, tutor_id, "tutor", "Dr. Tutor")
    await _create_user(db_session, student_id, "student", "Estudiante Uno")
    _, assignment_id = await _create_assignment(db_session, student_id, tutor_id)

    resp = await client.get(
        "/evaluations/my-students",
        headers=_auth(str(tutor_id), "tutor"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(student_id)
    assert data[0]["full_name"] == "Estudiante Uno"
    assert data[0]["assignment_id"] == str(assignment_id)


# ---------------------------------------------------------------------------
# Test 2: Tutor evalúa estudiante asignado → 201
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_evaluates_assigned_student(client: AsyncClient, db_session: AsyncSession):
    tutor_id = uuid.uuid4()
    student_id = uuid.uuid4()

    await _create_user(db_session, tutor_id, "tutor")
    await _create_user(db_session, student_id, "student")
    _, assignment_id = await _create_assignment(db_session, student_id, tutor_id)

    resp = await client.post(
        "/evaluations",
        json=_eval_payload(student_id, assignment_id),
        headers=_auth(str(tutor_id), "tutor"),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["tutor_id"] == str(tutor_id)
    assert data["student_id"] == str(student_id)
    assert data["assignment_id"] == str(assignment_id)
    assert len(data["items"]) == 2


# ---------------------------------------------------------------------------
# Test 3: Tutor intenta evaluar estudiante NO asignado → 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_cannot_evaluate_unassigned_student(client: AsyncClient, db_session: AsyncSession):
    tutor_id = uuid.uuid4()
    other_student_id = uuid.uuid4()
    fake_assignment_id = uuid.uuid4()

    await _create_user(db_session, tutor_id, "tutor")
    await _create_user(db_session, other_student_id, "student")

    resp = await client.post(
        "/evaluations",
        json=_eval_payload(other_student_id, fake_assignment_id),
        headers=_auth(str(tutor_id), "tutor"),
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Test 4: Estudiante ve sus propias evaluaciones → 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_views_own_evaluations(client: AsyncClient, db_session: AsyncSession):
    tutor_id = uuid.uuid4()
    student_id = uuid.uuid4()

    await _create_user(db_session, tutor_id, "tutor")
    await _create_user(db_session, student_id, "student")
    _, assignment_id = await _create_assignment(db_session, student_id, tutor_id)

    # Tutor crea evaluación
    await client.post(
        "/evaluations",
        json=_eval_payload(student_id, assignment_id),
        headers=_auth(str(tutor_id), "tutor"),
    )

    # Estudiante ve sus evaluaciones
    resp = await client.get(
        f"/evaluations/students/{student_id}",
        headers=_auth(str(student_id), "student"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 1
    assert data[0]["student_id"] == str(student_id)


# ---------------------------------------------------------------------------
# Test 5: Estudiante intenta ver evaluaciones de otro estudiante → 403
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_cannot_view_other_student_evaluations(client: AsyncClient, db_session: AsyncSession):
    student_a = uuid.uuid4()
    student_b = uuid.uuid4()

    await _create_user(db_session, student_a, "student")
    await _create_user(db_session, student_b, "student")

    resp = await client.get(
        f"/evaluations/students/{student_b}",
        headers=_auth(str(student_a), "student"),
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# Test 6: Coordinador puede ver evaluaciones de cualquier estudiante → 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_coordinator_views_any_student_evaluations(client: AsyncClient, db_session: AsyncSession):
    tutor_id = uuid.uuid4()
    student_id = uuid.uuid4()
    coordinator_id = uuid.uuid4()

    await _create_user(db_session, tutor_id, "tutor")
    await _create_user(db_session, student_id, "student")
    _, assignment_id = await _create_assignment(db_session, student_id, tutor_id)

    # Tutor crea evaluación
    await client.post(
        "/evaluations",
        json=_eval_payload(student_id, assignment_id),
        headers=_auth(str(tutor_id), "tutor"),
    )

    # Coordinador ve evaluaciones del estudiante
    resp = await client.get(
        f"/evaluations/students/{student_id}",
        headers=_auth(str(coordinator_id), "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 1


# ---------------------------------------------------------------------------
# Test 7 (PBT): Para cualquier student_id no asignado al tutor → 403
# Validates: Requirements 5.3
# ---------------------------------------------------------------------------

@given(
    unassigned_student_id=st.uuids(),
    fake_assignment_id=st.uuids(),
)
@h_settings(max_examples=20)
def test_p1_unassigned_student_evaluation_returns_403(
    unassigned_student_id: uuid.UUID,
    fake_assignment_id: uuid.UUID,
):
    """
    **Validates: Requirements 5.3**

    P1: Para cualquier student_id no asignado al tutor autenticado,
    POST /evaluations retorna 403.
    """
    async def _run():
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)

        import app.models  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        tutor_id = uuid.uuid4()

        async with session_factory() as session:
            async def override_get_db():
                yield session

            fastapi_app.dependency_overrides[get_db] = override_get_db

            async with AsyncClient(
                transport=ASGITransport(app=fastapi_app), base_url="http://test"
            ) as ac:
                resp = await ac.post(
                    "/evaluations",
                    json={
                        "student_id": str(unassigned_student_id),
                        "assignment_id": str(fake_assignment_id),
                        "period_label": "Semana 1",
                        "overall_comment": None,
                        "items": [
                            {"dimension": "Actitud", "score": 5, "comment": None}
                        ],
                    },
                    headers=_auth(str(tutor_id), "tutor"),
                )
                status_code = resp.status_code

            fastapi_app.dependency_overrides.clear()

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()
        return status_code

    status_code = asyncio.run(_run())
    assert status_code == 403, (
        f"Esperado 403 pero obtuvo {status_code} "
        f"(student_id={unassigned_student_id}, assignment_id={fake_assignment_id})"
    )
