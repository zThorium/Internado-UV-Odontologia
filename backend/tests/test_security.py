import pytest
from app.core.security import hash_password, verify_password


pytestmark = pytest.mark.unit


def test_hash_password_returns_string():
    hashed = hash_password("secret123")
    assert isinstance(hashed, str)
    assert hashed != "secret123"


def test_hash_password_produces_bcrypt_hash():
    hashed = hash_password("mypassword")
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_correct():
    hashed = hash_password("correct_password")
    assert verify_password("correct_password", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct_password")
    assert verify_password("wrong_password", hashed) is False


def test_hash_password_different_hashes_same_input():
    """bcrypt genera un salt aleatorio, por lo que dos hashes del mismo input difieren."""
    h1 = hash_password("same_password")
    h2 = hash_password("same_password")
    assert h1 != h2
    # pero ambos verifican correctamente
    assert verify_password("same_password", h1) is True
    assert verify_password("same_password", h2) is True


import time
from datetime import timedelta
from jose import JWTError, jwt
from app.core.security import create_access_token, decode_access_token
from app.core.config import settings


# --- create_access_token ---

def test_create_access_token_returns_string():
    token = create_access_token({"sub": "user-123", "role": "student"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_payload_contains_sub_and_role():
    token = create_access_token({"sub": "user-abc", "role": "tutor"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "user-abc"
    assert payload["role"] == "tutor"


def test_create_access_token_payload_contains_exp():
    token = create_access_token({"sub": "user-1", "role": "coordinator"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert "exp" in payload


def test_create_access_token_custom_expires_delta():
    token = create_access_token({"sub": "u", "role": "student"}, expires_delta=timedelta(seconds=5))
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert "exp" in payload


def test_create_access_token_expired_raises():
    token = create_access_token({"sub": "u", "role": "student"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_access_token(token)


# --- decode_access_token ---

def test_decode_access_token_valid():
    token = create_access_token({"sub": "user-xyz", "role": "student"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user-xyz"
    assert payload["role"] == "student"


def test_decode_access_token_invalid_raises():
    with pytest.raises(JWTError):
        decode_access_token("not.a.valid.token")


def test_decode_access_token_tampered_raises():
    token = create_access_token({"sub": "user-1", "role": "student"})
    tampered = token[:-4] + "xxxx"
    with pytest.raises(JWTError):
        decode_access_token(tampered)
