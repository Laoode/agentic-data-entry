"""Unit tests for password hashing helpers."""

from app.services.auth.passwords import hash_password, verify_password


def test_hash_and_verify_roundtrip():
    hashed = hash_password("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert verify_password("s3cret-pw", hashed) is True


def test_verify_rejects_wrong_password():
    hashed = hash_password("s3cret-pw")
    assert verify_password("wrong-pw", hashed) is False


def test_hash_is_salted_per_call():
    assert hash_password("same-pw") != hash_password("same-pw")


def test_verify_returns_false_on_malformed_hash():
    """The dev seed user row stores 'not-a-real-hash'; login against it must
    fail closed, never raise."""
    assert verify_password("anything", "not-a-real-hash") is False


def test_verify_returns_false_on_empty_hash():
    assert verify_password("anything", "") is False
