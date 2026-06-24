"""Tests sécurité : hachage mot de passe + JWT."""

import time

import pytest

from app.core.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("password123")
    assert h != "password123"
    assert verify_password("password123", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    tok = create_access_token("user-1", tenant_id="tenant-1")
    payload = decode_access_token(tok)
    assert payload["sub"] == "user-1"
    assert payload["tid"] == "tenant-1"


def test_jwt_tampered_rejected():
    tok = create_access_token("user-1", tenant_id="tenant-1")
    with pytest.raises(TokenError):
        decode_access_token(tok + "x")


def test_jwt_expired_rejected():
    tok = create_access_token("user-1", tenant_id="tenant-1", expires_minutes=-1)
    time.sleep(0.01)
    with pytest.raises(TokenError):
        decode_access_token(tok)
