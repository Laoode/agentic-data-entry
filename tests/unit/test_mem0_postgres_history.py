"""Tests for the mem0 PostgreSQL history hook."""

from importlib.metadata import version

from app.services.core.memory_history import (
    SUPPORTED_MEM0_VERSION,
    PostgresHistoryStore,
    install_postgres_history_store,
)
from app.services.core.memory import MemoryService
from config.settings import Settings


def test_supported_mem0_version_matches_installed_package():
    assert version("mem0ai") == SUPPORTED_MEM0_VERSION


def test_install_replaces_mem0_sqlite_manager():
    from mem0.memory import main as mem0_memory

    install_postgres_history_store()

    assert mem0_memory.SQLiteManager is PostgresHistoryStore


def test_memory_service_sends_database_url_to_history_store(monkeypatch):
    from mem0 import AsyncMemory

    captured_config = {}
    fake_backend = object()

    def fake_from_config(config):
        captured_config.update(config)
        return fake_backend

    monkeypatch.setattr(AsyncMemory, "from_config", fake_from_config)
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://memory-user:memory-pass@db:5432/klaudia",
    )

    service = MemoryService.from_settings(settings)

    assert service is not None
    assert captured_config["history_db_path"] == settings.database_url
