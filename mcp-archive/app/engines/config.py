import os


def get_database_url() -> str:
    """Return the required PostgreSQL DSN.

    Raises:
        RuntimeError: If DATABASE_URL is missing.
    """
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for mcp-archive")
    return database_url
