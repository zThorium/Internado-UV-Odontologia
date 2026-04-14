from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

import app.core.keycloak_client as keycloak_client
import app.routers.auth as auth_router
from app.models.user import User


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_oauth_callback_refresh_logout_success_paths(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        keycloak_client,
        "exchange_code_for_token",
        lambda code, redirect: {
            "access_token": "a1",
            "refresh_token": "r1",
            "expires_in": 300,
            "token_type": "Bearer",
        },
    )
    monkeypatch.setattr(
        keycloak_client,
        "refresh_access_token",
        lambda refresh_token: {"access_token": "a2", "refresh_token": "r2", "expires_in": 300},
    )
    monkeypatch.setattr(keycloak_client, "logout_user", lambda refresh_token: None)

    callback = await client.post("/auth/callback", params={"code": "valid-code"})
    assert callback.status_code == 200, callback.text
    assert callback.json()["access_token"] == "a1"

    refresh = await client.post("/auth/refresh", params={"refresh_token": "r1"})
    assert refresh.status_code == 200, refresh.text
    assert refresh.json()["access_token"] == "a2"

    logout = await client.post("/auth/logout", params={"refresh_token": "r2"})
    assert logout.status_code == 200, logout.text
    assert "Sesión cerrada" in logout.json()["message"]


@pytest.mark.asyncio
async def test_oauth_callback_refresh_logout_error_paths(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(keycloak_client, "exchange_code_for_token", lambda code, redirect: (_ for _ in ()).throw(RuntimeError("invalid")))
    monkeypatch.setattr(keycloak_client, "refresh_access_token", lambda refresh_token: (_ for _ in ()).throw(RuntimeError("expired")))
    monkeypatch.setattr(keycloak_client, "logout_user", lambda refresh_token: (_ for _ in ()).throw(RuntimeError("logout error")))

    callback = await client.post("/auth/callback", params={"code": "invalid"})
    assert callback.status_code == 400

    refresh = await client.post("/auth/refresh", params={"refresh_token": "bad"})
    assert refresh.status_code == 401

    logout = await client.post("/auth/logout", params={"refresh_token": "bad"})
    assert logout.status_code == 400


@pytest.mark.asyncio
async def test_create_user_by_coordinator_success(
    client: AsyncClient,
    db_session,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    coordinator_id = "11111111-1111-1111-1111-111111111111"
    keycloak_id = "22aa22aa-22aa-42aa-82aa-22aa22aa22aa"

    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: True)
    monkeypatch.setattr(auth_router, "create_keycloak_user", lambda **kwargs: keycloak_id)
    monkeypatch.setattr(auth_router, "assign_role_to_keycloak_user", lambda user_id, role_name: None)

    resp = await client.post(
        "/auth/create-user",
        json={
            "email": "nuevo.estudiante@internado.cl",
            "password": "ClaveSegura123",
            "full_name": "Nuevo Estudiante",
            "role": "student",
        },
        headers=auth_headers(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == keycloak_id
    assert body["role"] == "student"

    created_user = (
        await db_session.execute(select(User).where(User.id == UUID(keycloak_id)))
    ).scalar_one_or_none()
    assert created_user is not None
    assert created_user.email == "nuevo.estudiante@internado.cl"


@pytest.mark.asyncio
async def test_create_user_returns_400_when_email_exists_locally(
    client: AsyncClient,
    create_user,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    coordinator_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    existing_email = "duplicado@internado.cl"
    await create_user("student", email=existing_email)

    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: True)

    resp = await client.post(
        "/auth/create-user",
        json={
            "email": existing_email,
            "password": "ClaveSegura123",
            "full_name": "Duplicado",
            "role": "student",
        },
        headers=auth_headers(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_user_returns_503_when_keycloak_unavailable(
    client: AsyncClient,
    auth_headers,
    monkeypatch: pytest.MonkeyPatch,
):
    coordinator_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    monkeypatch.setattr(auth_router, "is_keycloak_available", lambda: False)

    resp = await client.post(
        "/auth/create-user",
        json={
            "email": "nuevo.tutor@internado.cl",
            "password": "ClaveSegura123",
            "full_name": "Nuevo Tutor",
            "role": "tutor",
            "profession": "Dentista",
            "available_hours_per_week": 10,
            "tutor_training_status": "in_progress",
        },
        headers=auth_headers(coordinator_id, "coordinator"),
    )
    assert resp.status_code == 503
