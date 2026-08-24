"""Shared PostgreSQL fixtures for integration tests."""

from collections.abc import AsyncIterator

import pytest

from app.services.extraction.infra.db_client import AppDBClient
from config.settings import Settings
from tests.integration.postgres import POSTGRES_TEST_URL, reset_postgres_database


@pytest.fixture
async def postgres_db() -> AsyncIterator[AppDBClient]:
    """Provide a clean connection to the isolated PostgreSQL test database."""
    database = AppDBClient(Settings(_env_file=None, DATABASE_URL=POSTGRES_TEST_URL))
    try:
        await database.connect()
    except Exception:
        pytest.skip("The isolated PostgreSQL test database is unavailable")
    await reset_postgres_database(database)
    yield database
    await database.close()
