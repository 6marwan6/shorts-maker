"""Argon2id password hashing + rotating refresh tokens (impl plan §1.3: 'Argon2id password
hashing', 'rotating refresh tokens, CSRF protection and strict cookie attributes').

Access tokens are short-lived signed tokens (itsdangerous-style HMAC, stdlib hmac/hashlib --
no extra dependency beyond what impl plan §4.1 already lists). Refresh tokens are opaque
random strings; only their SHA-256 hash is ever persisted (models.RefreshToken.token_hash),
so a leaked database dump does not itself hand out usable refresh tokens.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


# --------------------------------------------------------------------------------------
# Refresh tokens (opaque, rotated; only the hash is stored)
# --------------------------------------------------------------------------------------

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------------------
# Access tokens: short-lived, signed, stateless (HMAC-SHA256 over "sub:exp", stdlib only)
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class AccessTokenPayload:
    subject: str  # user id, as string
    expires_at: int  # unix epoch seconds


class InvalidAccessToken(ValueError):
    pass


def issue_access_token(*, subject: str, secret_key: str, ttl_seconds: int, now: int | None = None) -> str:
    now = int(time.time()) if now is None else now
    exp = now + ttl_seconds
    payload = f"{subject}:{exp}"
    sig = hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_access_token(token: str, *, secret_key: str, now: int | None = None) -> AccessTokenPayload:
    now = int(time.time()) if now is None else now
    try:
        subject, exp_str, sig = token.split(":", 2)
        exp = int(exp_str)
    except (ValueError, AttributeError) as e:
        raise InvalidAccessToken("malformed token") from e
    expected_sig = hmac.new(secret_key.encode("utf-8"), f"{subject}:{exp}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise InvalidAccessToken("signature mismatch")
    if now >= exp:
        raise InvalidAccessToken("token expired")
    return AccessTokenPayload(subject=subject, expires_at=exp)
