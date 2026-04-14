"""
Tests unitarios exhaustivos para require_role().

Cubre:
- Matriz 3x3: cada rol de usuario vs cada rol permitido (9 combinaciones)
- Combinaciones multi-rol (allowed_roles con 2 elementos)
- Casos críticos del diseño: tutor bloqueado en bitácora y permitido en incidentes
"""
import pytest
from fastapi import HTTPException

from app.core.deps import get_current_user, require_role
from app.core.security import create_access_token


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _check(user_role: str, *allowed_roles: str):
    """Crea un usuario con user_role e invoca require_role(*allowed_roles)."""
    token = create_access_token({"sub": f"{user_role}-uid", "role": user_role})
    user = await get_current_user(token=token)
    checker = require_role(*allowed_roles)
    return await checker(current_user=user)


# ---------------------------------------------------------------------------
# Matriz 3x3 — acceso permitido (diagonal principal)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_accesses_student_endpoint_ok():
    result = await _check("student", "student")
    assert result.role == "student"


@pytest.mark.asyncio
async def test_tutor_accesses_tutor_endpoint_ok():
    result = await _check("tutor", "tutor")
    assert result.role == "tutor"


@pytest.mark.asyncio
async def test_coordinator_accesses_coordinator_endpoint_ok():
    result = await _check("coordinator", "coordinator")
    assert result.role == "coordinator"


# ---------------------------------------------------------------------------
# Matriz 3x3 — acceso denegado (fuera de la diagonal)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_accesses_tutor_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("student", "tutor")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_student_accesses_coordinator_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("student", "coordinator")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_tutor_accesses_student_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("tutor", "student")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_tutor_accesses_coordinator_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("tutor", "coordinator")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_coordinator_accesses_student_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("coordinator", "student")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_coordinator_accesses_tutor_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("coordinator", "tutor")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Combinaciones multi-rol: allowed = ["student", "coordinator"]
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_student_accesses_student_coordinator_endpoint_ok():
    result = await _check("student", "student", "coordinator")
    assert result.role == "student"


@pytest.mark.asyncio
async def test_coordinator_accesses_student_coordinator_endpoint_ok():
    result = await _check("coordinator", "student", "coordinator")
    assert result.role == "coordinator"


@pytest.mark.asyncio
async def test_tutor_accesses_student_coordinator_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("tutor", "student", "coordinator")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Combinaciones multi-rol: allowed = ["tutor", "coordinator"]
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_accesses_tutor_coordinator_endpoint_ok():
    result = await _check("tutor", "tutor", "coordinator")
    assert result.role == "tutor"


@pytest.mark.asyncio
async def test_coordinator_accesses_tutor_coordinator_endpoint_ok():
    result = await _check("coordinator", "tutor", "coordinator")
    assert result.role == "coordinator"


@pytest.mark.asyncio
async def test_student_accesses_tutor_coordinator_endpoint_raises_403():
    with pytest.raises(HTTPException) as exc:
        await _check("student", "tutor", "coordinator")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Casos críticos del diseño
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tutor_blocked_from_logbook_endpoint_raises_403():
    """Tutor intenta acceder a endpoint de bitácora (solo student+coordinator) → 403."""
    with pytest.raises(HTTPException) as exc:
        await _check("tutor", "student", "coordinator")
    assert exc.value.status_code == 403
    assert exc.value.detail == "Acceso denegado"


@pytest.mark.asyncio
async def test_tutor_allowed_in_incidents_endpoint_roles_ok():
    """Tutor puede acceder a endpoint de incidentes cuando allowed incluye tutor."""
    result = await _check("tutor", "student", "tutor", "coordinator")
    assert result.role == "tutor"


# ---------------------------------------------------------------------------
# Verificar que require_role retorna el UserInToken correcto al permitir acceso
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_require_role_returns_user_with_correct_id_and_role():
    token = create_access_token({"sub": "abc-123", "role": "coordinator"})
    user = await get_current_user(token=token)
    checker = require_role("coordinator")
    result = await checker(current_user=user)
    assert result.id == "abc-123"
    assert result.role == "coordinator"
