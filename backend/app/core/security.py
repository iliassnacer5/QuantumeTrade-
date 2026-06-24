"""Sécurité : hachage de mot de passe (PBKDF2) et JWT HS256.

Implémentation basée sur la stdlib (hashlib/hmac) pour rester portable et sans dépendance
native. En production, on peut basculer vers argon2 (passlib) et python-jose.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import get_settings

_PBKDF2_ROUNDS = 200_000


# ---------------- Mots de passe ----------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${_PBKDF2_ROUNDS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt_hex, dk_hex = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False


# ---------------- JWT HS256 ----------------
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def create_access_token(subject: str, *, tenant_id: str, expires_minutes: int | None = None) -> str:
    s = get_settings()
    exp_min = expires_minutes or s.access_token_expire_minutes
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "tid": tenant_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + exp_min * 60,
    }
    segments = [
        _b64url(json.dumps(header, separators=(",", ":")).encode()),
        _b64url(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    sig = hmac.new(s.secret_key.encode(), signing_input, hashlib.sha256).digest()
    segments.append(_b64url(sig))
    return ".".join(segments)


class TokenError(Exception):
    pass


def decode_access_token(token: str) -> dict:
    s = get_settings()
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise TokenError("format de token invalide") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(s.secret_key.encode(), signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url(expected), sig_b64):
        raise TokenError("signature invalide")

    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp", 0) < int(time.time()):
        raise TokenError("token expiré")
    return payload
