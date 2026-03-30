import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from app.core.deps import get_current_user, require_role, UserInToken
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    token = create_access_token({"sub": "user-123", "role": "student"})
    user = await get_current_user(token=token)
    assert isinstance(user, UserInToken)
    assert user.id == "user-123"
    assert user.role == "student"


@pytest.mark.asyncio
async def test_get_current_user_all_roles():
    for role in ("student", "tutor", "coordinator"):
        token = create_access_token({"sub": "uid", "role": role})
        user = await get_current_user(token=token)
        assert user.role == role


@pytest.mark.asyncio
async def test_get_current_user_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="invalid.token.here")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_expired_token_raises_401():
    from datetime import timedelta
    token = create_access_token({"sub": "u", "role": "student"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_sub_raises_401():
    # Token sin campo 'sub'
    token = create_access_token({"role": "student"})
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_role_raises_401():
    # Token sin campo 'role'
    token = create_access_token({"sub": "user-123"})
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token)
    assert exc_info.value.status_code == 401


# --- Tests para require_role ---

@pytest.mark.asyncio
async def test_require_role_tutor_accessing_student_endpoint_raises_403():
    """Tutor intentando acceder a endpoint de student → 403"""
    token = create_access_token({"sub": "tutor-1", "role": "tutor"})
    checker = require_role("student")
    with pytest.raises(HTTPException) as exc_info:
        user = await get_current_user(token=token)
        await checker(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_role_student_accessing_student_endpoint_ok():
    """Student accediendo a endpoint de student → OK"""
    token = create_access_token({"sub": "student-1", "role": "student"})
    checker = require_role("student")
    user = await get_current_user(token=token)
    result = await checker(current_user=user)
    assert result.role == "student"
    assert result.id == "student-1"


@pytest.mark.asyncio
async def test_require_role_coordinator_accessing_student_coordinator_endpoint_ok():
    """Coordinator accediendo a endpoint de student+coordinator → OK"""
    token = create_access_token({"sub": "coord-1", "role": "coordinator"})
    checker = require_role("student", "coordinator")
    user = await get_current_user(token=token)
    result = await checker(current_user=user)
    assert result.role == "coordinator"


@pytest.mark.asyncio
async def test_require_role_tutor_accessing_tutor_endpoint_ok():
    """Tutor accediendo a endpoint de tutor → OK"""
    token = create_access_token({"sub": "tutor-2", "role": "tutor"})
    checker = require_role("tutor")
    user = await get_current_user(token=token)
    result = await checker(current_user=user)
    assert result.role == "tutor"
