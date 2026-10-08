"""Phase 1 unit tests: app.auth primitives, pure functions -- no DB, no network."""
import time

import pytest
from app import auth


def test_password_hash_and_verify_roundtrip():
    hashed = auth.hash_password("correct horse battery staple")
    assert auth.verify_password("correct horse battery staple", hashed)


def test_password_verify_rejects_wrong_password():
    hashed = auth.hash_password("correct horse battery staple")
    assert not auth.verify_password("wrong password", hashed)


def test_password_hash_is_salted_and_not_reused_verbatim():
    h1 = auth.hash_password("same password")
    h2 = auth.hash_password("same password")
    assert h1 != h2  # Argon2id includes a random salt per hash


def test_refresh_token_is_opaque_and_hash_is_deterministic():
    raw = auth.generate_refresh_token()
    assert len(raw) > 32
    h1 = auth.hash_refresh_token(raw)
    h2 = auth.hash_refresh_token(raw)
    assert h1 == h2
    assert h1 != raw  # never store the raw token, only its hash


def test_refresh_tokens_are_unique():
    tokens = {auth.generate_refresh_token() for _ in range(50)}
    assert len(tokens) == 50


def test_access_token_roundtrip():
    token = auth.issue_access_token(subject="user-123", secret_key="secret", ttl_seconds=900)
    payload = auth.verify_access_token(token, secret_key="secret")
    assert payload.subject == "user-123"


def test_access_token_expired_is_rejected():
    now = int(time.time())
    token = auth.issue_access_token(subject="user-123", secret_key="secret", ttl_seconds=1, now=now - 10)
    with pytest.raises(auth.InvalidAccessToken):
        auth.verify_access_token(token, secret_key="secret", now=now)


def test_access_token_wrong_secret_is_rejected():
    token = auth.issue_access_token(subject="user-123", secret_key="secret-a", ttl_seconds=900)
    with pytest.raises(auth.InvalidAccessToken):
        auth.verify_access_token(token, secret_key="secret-b")


def test_access_token_tampered_subject_is_rejected():
    token = auth.issue_access_token(subject="user-123", secret_key="secret", ttl_seconds=900)
    _subject, exp, sig = token.split(":", 2)
    tampered = f"user-999:{exp}:{sig}"
    with pytest.raises(auth.InvalidAccessToken):
        auth.verify_access_token(tampered, secret_key="secret")


def test_access_token_malformed_is_rejected():
    with pytest.raises(auth.InvalidAccessToken):
        auth.verify_access_token("not-a-real-token", secret_key="secret")
