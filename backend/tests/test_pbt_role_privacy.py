"""
Tests de propiedad (Property-Based Testing) con hypothesis para control de acceso por rol.

Valida: Requirements 2.4, 2.10, 2.11

Propiedades verificadas:
- P1: Para cualquier user_id, role="tutor" es bloqueado por require_role("student", "coordinator") → 403
- P2: Para cualquier user_id, role="tutor" es bloqueado por require_role("student") → 403
- P3: Para cualquier user_id, role="tutor" es bloqueado por require_role("coordinator") → 403
- P4: Para cualquier user_id y role en ["student", "coordinator"], require_role("student", "coordinator") permite acceso
- P5: Para cualquier user_id, role="student" es bloqueado por require_role("tutor") → 403
"""
import asyncio

import pytest
from fastapi import HTTPException
from hypothesis import given, settings, strategies as st

from app.core.deps import get_current_user, require_role
from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# Helper síncrono (hypothesis no soporta async nativamente)
# ---------------------------------------------------------------------------

def _run_role_check(user_id: str, user_role: str, *allowed_roles: str):
    """Crea token con user_id y user_role, invoca require_role(*allowed_roles). Síncrono."""
    async def _inner():
        token = create_access_token({"sub": user_id, "role": user_role})
        user = await get_current_user(token=token)
        checker = require_role(*allowed_roles)
        return await checker(current_user=user)

    return asyncio.run(_inner())


# ---------------------------------------------------------------------------
# P1: Tutor bloqueado por require_role("student", "coordinator") — endpoints bitácora/incidentes
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

@given(user_id=st.uuids().map(str))
@settings(max_examples=50)
def test_p1_tutor_blocked_by_student_coordinator_role(user_id: str):
    """
    **Validates: Requirements 2.4**

    P1: Para cualquier user_id, un token con role="tutor" siempre es bloqueado
    por require_role("student", "coordinator") con 403.
    """
    with pytest.raises(HTTPException) as exc_info:
        _run_role_check(user_id, "tutor", "student", "coordinator")
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# P2: Tutor bloqueado por require_role("student")
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

@given(user_id=st.uuids().map(str))
@settings(max_examples=50)
def test_p2_tutor_blocked_by_student_only_role(user_id: str):
    """
    **Validates: Requirements 2.4**

    P2: Para cualquier user_id, un token con role="tutor" siempre es bloqueado
    por require_role("student") con 403.
    """
    with pytest.raises(HTTPException) as exc_info:
        _run_role_check(user_id, "tutor", "student")
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# P3: Tutor bloqueado por require_role("coordinator")
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

@given(user_id=st.uuids().map(str))
@settings(max_examples=50)
def test_p3_tutor_blocked_by_coordinator_only_role(user_id: str):
    """
    **Validates: Requirements 2.4**

    P3: Para cualquier user_id, un token con role="tutor" siempre es bloqueado
    por require_role("coordinator") con 403.
    """
    with pytest.raises(HTTPException) as exc_info:
        _run_role_check(user_id, "tutor", "coordinator")
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# P4: student y coordinator siempre permitidos por require_role("student", "coordinator")
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

@given(
    user_id=st.uuids().map(str),
    user_role=st.sampled_from(["student", "coordinator"]),
)
@settings(max_examples=50)
def test_p4_student_and_coordinator_allowed(user_id: str, user_role: str):
    """
    **Validates: Requirements 2.4**

    P4: Para cualquier user_id y role en ["student", "coordinator"],
    require_role("student", "coordinator") siempre permite el acceso (no lanza 403).
    """
    result = _run_role_check(user_id, user_role, "student", "coordinator")
    assert result.role == user_role
    assert result.id == user_id


# ---------------------------------------------------------------------------
# P5: student bloqueado por require_role("tutor")
# Validates: Requirements 2.4
# ---------------------------------------------------------------------------

@given(user_id=st.uuids().map(str))
@settings(max_examples=50)
def test_p5_student_blocked_by_tutor_only_role(user_id: str):
    """
    **Validates: Requirements 2.4**

    P5: Para cualquier user_id, un token con role="student" siempre es bloqueado
    por require_role("tutor") con 403.
    """
    with pytest.raises(HTTPException) as exc_info:
        _run_role_check(user_id, "student", "tutor")
    assert exc_info.value.status_code == 403
