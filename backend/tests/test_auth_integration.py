from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select

import app.routers.auth as auth_router
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.user import User


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_forgot_password_sends_email_for_existing_active_user(
    client: AsyncClient,
    create_user,
    monkeypatch: pytest.MonkeyPatch,
):
    user = await create_user("student", email="forgot@internado.cl")
    mocked_sender = AsyncMock()
    monkeypatch.setattr(auth_router, "send_reset_password_email", mocked_sender)

    resp = await client.post("/auth/forgot-password", json={"email": user.email})
    assert resp.status_code == 200, resp.text
    assert "Si el email existe" in resp.json()["message"]
    assert mocked_sender.await_count == 1
    args = mocked_sender.await_args.args
    assert args[0] == user.email
    assert isinstance(args[1], str)


@pytest.mark.asyncio
async def test_forgot_password_is_silent_when_email_not_found(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    mocked_sender = AsyncMock()
    monkeypatch.setattr(auth_router, "send_reset_password_email", mocked_sender)

    resp = await client.post("/auth/forgot-password", json={"email": "missing@internado.cl"})
    assert resp.status_code == 200, resp.text
    assert mocked_sender.await_count == 0


@pytest.mark.asyncio
async def test_reset_password_with_valid_token_updates_hash(
    client: AsyncClient,
    db_session,
    create_user,
):
    user = await create_user("student", email="reset@internado.cl")
    token = create_access_token({"sub": str(user.id), "role": "student", "type": "reset"})

    resp = await client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "Nuev4ClaveSegura"},
    )
    assert resp.status_code == 200, resp.text

    updated_user = (
        await db_session.execute(select(User).where(User.id == user.id))
    ).scalar_one()
    assert verify_password("Nuev4ClaveSegura", updated_user.hashed_password) is True


@pytest.mark.asyncio
async def test_complete_onboarding_marks_user_and_is_idempotent(
    client: AsyncClient,
    db_session,
    create_user,
    auth_headers,
):
    user = await create_user("student", full_name="Onboarding User")

    first = await client.post(
        "/auth/complete-onboarding",
        headers=auth_headers(str(user.id), "student"),
    )
    assert first.status_code == 200, first.text

    second = await client.post(
        "/auth/complete-onboarding",
        headers=auth_headers(str(user.id), "student"),
    )
    assert second.status_code == 200, second.text

    updated_user = (
        await db_session.execute(select(User).where(User.id == user.id))
    ).scalar_one()
    assert updated_user.has_completed_onboarding is True


@pytest.mark.asyncio
async def test_login_uses_local_fallback_when_keycloak_is_unavailable(
    client: AsyncClient,
    create_user,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", False)
    user = await create_user("student", email="login503@internado.cl")
    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: False)
    monkeypatch.setattr(auth_router, "verify_password", lambda plain, hashed: True)

    resp = await client.post(
        "/auth/login",
        json={"email": user.email, "password": "irrelevant"},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert isinstance(payload["refresh_token"], str)


@pytest.mark.asyncio
async def test_login_rejects_inactive_user_before_password_grant(
    client: AsyncClient,
    create_user,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", False)
    user = await create_user("student", email="inactive@internado.cl", is_active=False)
    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: True)

    resp = await client.post(
        "/auth/login",
        json={"email": user.email, "password": "any-password"},
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_login_returns_oidc_tokens_for_active_user(
    client: AsyncClient,
    create_user,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", False)
    user = await create_user(
        "student",
        email="active@internado.cl",
        full_name="Active User",
    )

    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: True)
    monkeypatch.setattr(
        auth_router,
        "login_with_password",
        lambda username, password: {
            "access_token": "access-123",
            "refresh_token": "refresh-123",
            "expires_in": 300,
            "token_type": "bearer",
        },
    )

    resp = await client.post(
        "/auth/login",
        json={"email": user.email, "password": "valid-password"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"] == "access-123"
    assert data["refresh_token"] == "refresh-123"
    assert data["token_type"] == "bearer"
    assert data["has_completed_onboarding"] is False
