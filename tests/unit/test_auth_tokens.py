"""Unit tests for JWT access-token helpers."""

import datetime

import pytest

from app.services.auth.tokens import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)

_SECRET = "unit-test-secret-with-32-plus-bytes!"


def test_create_and_decode_roundtrip():
    token = create_access_token(user_id=42, secret=_SECRET)
    assert decode_access_token(token, secret=_SECRET) == 42


def test_decode_rejects_wrong_secret():
    token = create_access_token(user_id=42, secret=_SECRET)
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret="other-secret")


def test_decode_rejects_expired_token():
    token = create_access_token(
        user_id=42,
        secret=_SECRET,
        expires_delta=datetime.timedelta(seconds=-1),
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret=_SECRET)


def test_decode_rejects_garbage():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not.a.jwt", secret=_SECRET)


def test_decode_rejects_token_without_subject():
    import jwt

    token = jwt.encode({"foo": "bar"}, _SECRET, algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, secret=_SECRET)
