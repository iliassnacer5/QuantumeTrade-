"""TOTP (RFC 6238) — implémentation stdlib pour la MFA, sans dépendance externe.

Compatible Google Authenticator / Authy (HMAC-SHA1, période 30s, 6 chiffres).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


def generate_secret() -> str:
    """Secret base32 (160 bits) à enregistrer dans l'app d'authentification."""
    return base64.b32encode(secrets.token_bytes(20)).decode("utf-8").rstrip("=")


def _hotp(secret_b32: str, counter: int, digits: int = 6) -> str:
    # Recompose le padding base32
    pad = "=" * ((8 - len(secret_b32) % 8) % 8)
    key = base64.b32decode(secret_b32.upper() + pad)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(code).zfill(digits)


def totp_now(secret_b32: str, period: int = 30) -> str:
    return _hotp(secret_b32, int(time.time()) // period)


def verify(secret_b32: str, code: str, period: int = 30, window: int = 1) -> bool:
    """Vérifie un code TOTP avec tolérance +/- `window` périodes (dérive d'horloge)."""
    if not code or not code.isdigit():
        return False
    counter = int(time.time()) // period
    for delta in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret_b32, counter + delta), code):
            return True
    return False


def provisioning_uri(secret_b32: str, account: str, issuer: str = "Quantum Trade AI") -> str:
    """URI otpauth:// pour générer le QR code côté client."""
    label = quote(f"{issuer}:{account}")
    return f"otpauth://totp/{label}?secret={secret_b32}&issuer={quote(issuer)}&period=30&digits=6"
