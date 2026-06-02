from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests
from jose import jwt as jose_jwt

import app.core.keycloak_client as kc
from app.core.security import create_access_token


pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def reset_keycloak_availability_cache() -> None:
    kc._keycloak_availability_cache["value"] = None
    kc._keycloak_availability_cache["checked_at"] = 0.0


class _DummyResponse:
    def __init__(
        self,
        status_code: int = 200,
        json_data: dict | list | None = None,
        headers: dict | None = None,
        text: str = "",
        reason: str = "",
    ):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}
        self.headers = headers or {}
        self.text = text
        self.reason = reason

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


def test_validate_token_returns_info_when_active(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "introspect", lambda token: {"active": True, "sub": "u-1"})
    info = kc.validate_token("token")
    assert info["active"] is True
    assert info["sub"] == "u-1"


def test_validate_token_raises_value_error_when_inactive(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "introspect", lambda token: {"active": False})
    with pytest.raises(ValueError):
        kc.validate_token("token")


def test_get_user_info_delegates_to_keycloak_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "userinfo", lambda token: {"sub": "abc", "email": "a@test"})
    assert kc.get_user_info("token")["sub"] == "abc"


def test_exchange_code_for_token_propagates_keycloak_error(monkeypatch: pytest.MonkeyPatch):
    def _raise(*args, **kwargs):
        raise RuntimeError("invalid code")

    monkeypatch.setattr(kc.keycloak_openid, "token", _raise)
    with pytest.raises(RuntimeError):
        kc.exchange_code_for_token("bad", "http://redirect")


def test_login_with_password_returns_token_dict(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "token", lambda **kwargs: {"access_token": "abc"})
    tokens = kc.login_with_password("user@test", "secret")
    assert tokens["access_token"] == "abc"


def test_refresh_access_token_returns_new_access_token(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "refresh_token", lambda token: {"access_token": "new"})
    assert kc.refresh_access_token("refresh")["access_token"] == "new"


def test_logout_user_propagates_errors(monkeypatch: pytest.MonkeyPatch):
    def _raise(refresh_token: str):
        raise RuntimeError("logout error")

    monkeypatch.setattr(kc.keycloak_openid, "logout", _raise)
    with pytest.raises(RuntimeError):
        kc.logout_user("refresh")


def test_decode_token_without_validation_reads_claims():
    token = create_access_token({"sub": "user-1", "role": "student"})
    claims = kc.decode_token(token, validate=False)
    assert claims["sub"] == "user-1"


def test_decode_token_with_validation_uses_formatted_public_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "public_key", lambda: "PUBLIC_KEY_NO_PEM")
    monkeypatch.setattr(jose_jwt, "decode", lambda *args, **kwargs: {"sub": "validated-user"})
    claims = kc.decode_token("signed-token", validate=True)
    assert claims["sub"] == "validated-user"


def test_extract_roles_filters_to_application_roles():
    payload = {"realm_access": {"roles": ["offline_access", "student", "admin"]}}
    assert kc.extract_roles(payload) == ["student"]


def test_get_primary_role_returns_first_or_none():
    assert kc.get_primary_role({"realm_access": {"roles": ["tutor", "student"]}}) == "tutor"
    assert kc.get_primary_role({"realm_access": {"roles": ["manage-account"]}}) is None


def test_is_keycloak_available_returns_true_when_well_known_works(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc.keycloak_openid, "well_known", lambda: {"issuer": "http://localhost"})
    assert kc.is_keycloak_available() is True


def test_is_keycloak_available_returns_false_on_exception(monkeypatch: pytest.MonkeyPatch):
    def _raise():
        raise RuntimeError("down")

    monkeypatch.setattr(kc.keycloak_openid, "well_known", _raise)
    assert kc.is_keycloak_available() is False


def test_get_keycloak_admin_returns_instance(monkeypatch: pytest.MonkeyPatch):
    sentinel = Mock(name="KeycloakAdminInstance")
    monkeypatch.setattr("keycloak.KeycloakAdmin", lambda **kwargs: sentinel)
    assert kc.get_keycloak_admin() is sentinel


def test_get_admin_access_token_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: _DummyResponse(json_data={"access_token": "admin-token"}))
    assert kc._get_admin_access_token() == "admin-token"


def test_get_admin_access_token_timeout(monkeypatch: pytest.MonkeyPatch):
    def _timeout(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "post", _timeout)
    with pytest.raises(Exception, match="timeout"):
        kc._get_admin_access_token()


def test_create_keycloak_user_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc, "_get_admin_access_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _DummyResponse(json_data=[]))
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: _DummyResponse(
            status_code=201,
            headers={"location": "http://localhost/admin/realms/internado-uv/users/abc-123"},
        ),
    )

    created_id = kc.create_keycloak_user("student@test.local", "password123", "Student", "Test")
    assert created_id == "abc-123"


def test_create_keycloak_user_raises_if_email_exists(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc, "_get_admin_access_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _DummyResponse(json_data=[{"id": "existing"}]))

    with pytest.raises(ValueError, match="ya existe"):
        kc.create_keycloak_user("student@test.local", "password123", "Student", "Test")


def test_assign_role_to_keycloak_user_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc, "_get_admin_access_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _DummyResponse(json_data=[{"name": "student", "id": "role-1"}]))
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: _DummyResponse(status_code=204))

    kc.assign_role_to_keycloak_user("user-1", "student")


def test_assign_role_to_keycloak_user_raises_for_unknown_role(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc, "_get_admin_access_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _DummyResponse(json_data=[{"name": "student", "id": "role-1"}]))

    with pytest.raises(ValueError, match="no existe"):
        kc.assign_role_to_keycloak_user("user-1", "coordinator")


def test_delete_keycloak_user_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(kc, "_get_admin_access_token", lambda: "admin-token")
    monkeypatch.setattr(requests, "delete", lambda *args, **kwargs: _DummyResponse(status_code=204))

    kc.delete_keycloak_user("user-1")
