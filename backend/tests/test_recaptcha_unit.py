from __future__ import annotations

import pytest

from app.core.config import settings
from app.services.recaptcha import verify_recaptcha


pytestmark = pytest.mark.unit


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, payload: dict | None = None, fail: bool = False):
        self._payload = payload or {"success": True}
        self._fail = fail

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url: str, data: dict, timeout: float):
        if self._fail:
            raise RuntimeError("network error")
        return _FakeResponse(self._payload)


@pytest.mark.asyncio
async def test_verify_recaptcha_disabled_returns_true(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", False)
    assert await verify_recaptcha(token="", remote_ip=None) is True


@pytest.mark.asyncio
async def test_verify_recaptcha_enabled_without_token_returns_false(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", True)
    assert await verify_recaptcha(token="", remote_ip=None) is False


@pytest.mark.asyncio
async def test_verify_recaptcha_enabled_with_success_response(monkeypatch: pytest.MonkeyPatch):
    import app.services.recaptcha as recaptcha_module

    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", True)
    monkeypatch.setattr(recaptcha_module.httpx, "AsyncClient", lambda: _FakeAsyncClient(payload={"success": True}))

    assert await verify_recaptcha(token="token-ok", remote_ip="127.0.0.1") is True


@pytest.mark.asyncio
async def test_verify_recaptcha_fail_open_on_network_error(monkeypatch: pytest.MonkeyPatch):
    import app.services.recaptcha as recaptcha_module

    monkeypatch.setattr(settings, "RECAPTCHA_ENABLED", True)
    monkeypatch.setattr(recaptcha_module.httpx, "AsyncClient", lambda: _FakeAsyncClient(fail=True))

    assert await verify_recaptcha(token="token", remote_ip="127.0.0.1") is True
