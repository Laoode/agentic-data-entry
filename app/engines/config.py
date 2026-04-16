import os
from pathlib import Path

# DB path: relative to project root
DB_PATH = os.getenv("SQLITE_DB", "app_dev.db")


def get_db_path() -> str:
    """Resolve absolute path for the SQLite database."""
    path = Path(DB_PATH)
    if not path.is_absolute():
        # Resolve relative to the project root (two levels up from this file)
        project_root = Path(__file__).resolve().parents[3]
        path = project_root / path
    return str(path)
