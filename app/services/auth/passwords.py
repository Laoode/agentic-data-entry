"""Password hashing built on bcrypt.

bcrypt embeds a per-call random salt in the hash, so equal passwords never
produce equal hashes and verification needs no separate salt storage.
"""

import logging

import bcrypt

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a plaintext password.

    Args:
        password: Plaintext password.

    Returns:
        bcrypt hash string safe to store in the user table.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored hash.

    Fails closed: any malformed or legacy hash (e.g. the dev seed user's
    'not-a-real-hash') returns False instead of raising, so those accounts
    simply cannot log in.

    Args:
        password: Plaintext candidate password.
        password_hash: Stored bcrypt hash.

    Returns:
        True only when the password matches a well-formed hash.
    """
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        logger.warning("verify_password: malformed hash in user table")
        return False
