"""Chiffrement symétrique authentifié des secrets sensibles (clés API broker) — Phase 4.

Garde-fou : les clés API broker ne sont JAMAIS stockées en clair. Révocable : supprimer
l'enregistrement suffit.

Implémentation 100% stdlib (cohérent avec le reste du projet : JWT/PBKDF2 sans dépendance native).
Construction = stream cipher à base de HMAC-SHA256 (keystream en mode compteur) + Encrypt-then-MAC :
- clés `enc`/`mac` dérivées du secret applicatif (domaines séparés) ;
- format : base64( nonce[16] || ciphertext || tag[32] ), tag = HMAC(mac_key, nonce || ciphertext) ;
- déchiffrement à vérification constante (hmac.compare_digest) contre toute altération.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from app.core.config import get_settings

_NONCE = 16
_TAG = 32


def _keys() -> tuple[bytes, bytes]:
    root = get_settings().secret_key.encode()
    enc = hashlib.sha256(b"qta-enc:" + root).digest()
    mac = hashlib.sha256(b"qta-mac:" + root).digest()
    return enc, mac


def _keystream(enc_key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(enc_key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt(plaintext: str) -> str:
    enc_key, mac_key = _keys()
    nonce = secrets.token_bytes(_NONCE)
    data = plaintext.encode()
    ct = bytes(b ^ k for b, k in zip(data, _keystream(enc_key, nonce, len(data))))
    tag = hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(nonce + ct + tag).decode()


def decrypt(token: str) -> str:
    enc_key, mac_key = _keys()
    blob = base64.urlsafe_b64decode(token.encode())
    if len(blob) < _NONCE + _TAG:
        raise ValueError("jeton chiffré invalide")
    nonce, ct, tag = blob[:_NONCE], blob[_NONCE:-_TAG], blob[-_TAG:]
    expected = hmac.new(mac_key, nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("intégrité invalide (secret modifié ou donnée corrompue)")
    data = bytes(b ^ k for b, k in zip(ct, _keystream(enc_key, nonce, len(ct))))
    return data.decode()


def mask(secret: str, visible: int = 4) -> str:
    """Aperçu non sensible pour l'UI : ne révèle que les derniers caractères."""
    if not secret:
        return ""
    return ("•" * max(0, len(secret) - visible)) + secret[-visible:]
