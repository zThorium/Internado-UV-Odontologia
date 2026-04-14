from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import deps as deps_module
from app.core.security import create_access_token
from app.db.session import Base, get_db
from app.main import app as fastapi_app
from app.models.assignment import Assignment
from app.models.attendance import AttendanceRecord
from app.models.cohort import Cohort
from app.models.logbook import LogbookEntry, LogbookProcedure
from app.models.user import User


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def oidc_auth_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Simula validacion OIDC para tests sin depender de un servidor Keycloak real.
    """

    def _decode_token_for_tests(token: str, validate: bool = False) -> dict:
        claims = jwt.get_unverified_claims(token)

        # Compatibilidad con tokens de pruebas que traen role legacy.
        role = claims.get("role")
        realm_access = claims.get("realm_access")
        if role and not (isinstance(realm_access, dict) and isinstance(realm_access.get("roles"), list)):
            claims["realm_access"] = {"roles": [role]}

        return claims

    def _validate_token_for_tests(token: str) -> dict:
        try:
            claims = jwt.get_unverified_claims(token)
        except Exception:
            return {"active": False}

        exp = claims.get("exp")
        if isinstance(exp, (int, float)) and float(exp) < datetime.now(timezone.utc).timestamp():
            return {"active": False}

        return {"active": True}

    monkeypatch.setattr(deps_module, "_looks_like_keycloak_token", lambda token: True)
    monkeypatch.setattr(deps_module, "is_keycloak_available", lambda: True)
    monkeypatch.setattr(deps_module, "validate_token", _validate_token_for_tests)
    monkeypatch.setattr(deps_module, "decode_token", _decode_token_for_tests)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
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
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def make_token() -> Callable[[str, str], str]:
    def _build(user_id: str, role: str) -> str:
        return create_access_token(
            {
                "sub": user_id,
                "role": role,
                "iss": "http://localhost:8080/realms/internado-uv",
                "realm_access": {"roles": [role]},
            }
        )

    return _build


@pytest.fixture
def auth_headers(make_token: Callable[[str, str], str]) -> Callable[[str, str], dict[str, str]]:
    def _build(user_id: str, role: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {make_token(user_id, role)}"}

    return _build


@pytest.fixture
def random_uuid() -> Callable[[], str]:
    return lambda: str(uuid.uuid4())


@pytest_asyncio.fixture
async def create_user(db_session: AsyncSession) -> Callable[..., User]:
    async def _create(
        role: str,
        full_name: str | None = None,
        email: str | None = None,
        user_id: uuid.UUID | None = None,
        is_active: bool = True,
    ) -> User:
        uid = user_id or uuid.uuid4()
        user = User(
            id=uid,
            email=email or f"{uid}@internado.cl",
            hashed_password="hashed",
            full_name=full_name or f"{role.title()} Test",
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create


@pytest_asyncio.fixture
async def create_cohort(db_session: AsyncSession) -> Callable[..., Cohort]:
    async def _create(
        name: str = "Cohorte de Prueba",
        year: int = 2026,
        semester: int = 1,
        is_active: bool = True,
        cohort_id: uuid.UUID | None = None,
    ) -> Cohort:
        cohort = Cohort(
            id=cohort_id or uuid.uuid4(),
            name=name,
            year=year,
            semester=semester,
            is_active=is_active,
        )
        db_session.add(cohort)
        await db_session.commit()
        await db_session.refresh(cohort)
        return cohort

    return _create


@pytest_asyncio.fixture
async def create_assignment(db_session: AsyncSession) -> Callable[..., Assignment]:
    async def _create(
        student_id: uuid.UUID,
        tutor_id: uuid.UUID,
        cohort_id: uuid.UUID,
        care_level: str = "primary",
        clinical_site: str = "Clinica UV",
        start_date: date = date(2026, 1, 1),
        end_date: date = date(2026, 6, 30),
        is_active: bool = True,
        assignment_id: uuid.UUID | None = None,
    ) -> Assignment:
        assignment = Assignment(
            id=assignment_id or uuid.uuid4(),
            student_id=student_id,
            tutor_id=tutor_id,
            cohort_id=cohort_id,
            care_level=care_level,
            clinical_site=clinical_site,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
        )
        db_session.add(assignment)
        await db_session.commit()
        await db_session.refresh(assignment)
        return assignment

    return _create


@pytest_asyncio.fixture
async def create_attendance_record(db_session: AsyncSession) -> Callable[..., AttendanceRecord]:
    async def _create(
        student_id: uuid.UUID,
        attendance_date: date,
        status: str,
        observation: str | None = None,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            student_id=student_id,
            date=attendance_date,
            status=status,
            observation=observation,
        )
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)
        return record

    return _create


@pytest_asyncio.fixture
async def create_logbook_entry(db_session: AsyncSession) -> Callable[..., LogbookEntry]:
    async def _create(
        student_id: uuid.UUID,
        cohort_id: uuid.UUID,
        week_number: int,
        wellbeing_status: str | None = "good",
        status: str = "draft",
        week_start_date: date = date(2026, 1, 5),
    ) -> LogbookEntry:
        entry = LogbookEntry(
            student_id=student_id,
            cohort_id=cohort_id,
            week_number=week_number,
            week_start_date=week_start_date,
            wellbeing_status=wellbeing_status,
            status=status,
        )
        db_session.add(entry)
        await db_session.flush()

        procedure = LogbookProcedure(
            entry_id=entry.id,
            name="Examen y diagnóstico",
            description="Procedimiento de prueba",
            quantity=1,
        )
        db_session.add(procedure)
        await db_session.commit()
        await db_session.refresh(entry)
        return entry

    return _create