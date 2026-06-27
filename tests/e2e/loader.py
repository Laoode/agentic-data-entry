"""Load and validate the YAML dataset.

The dataset lives in `tests/e2e/dataset/cases/*.yaml`. Each file is a YAML list
of case mappings. We parse every file, validate each case against the pydantic
`Case` schema (fail fast with a clear message on the offending file), resolve
attachment paths to absolute, and return the cases in stable (file, order).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from tests.e2e.schema import Case

# tests/e2e/loader.py → repo root is two parents up.
REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = Path(__file__).resolve().parent / "dataset" / "cases"


def _resolve_attachment(rel: str) -> Path:
    """Resolve an attachment path (relative to repo root) and assert it exists."""
    p = (REPO_ROOT / rel).resolve()
    if not p.is_file():
        raise FileNotFoundError(
            f"attachment {rel!r} not found at {p} (paths are relative to repo root)"
        )
    return p


def load_cases(cases_dir: Path | None = None) -> list[Case]:
    """Return all validated cases, sorted by id.

    Raises ValueError with the file name if any case fails schema validation,
    so a malformed dataset is caught at collection time rather than mid-run.
    """
    directory = cases_dir or CASES_DIR
    files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))
    if not files:
        raise FileNotFoundError(f"no dataset files in {directory}")

    cases: list[Case] = []
    seen_ids: set[str] = set()
    for f in files:
        raw = yaml.safe_load(f.read_text()) or []
        if not isinstance(raw, list):
            raise ValueError(f"{f.name}: top level must be a YAML list of cases")
        for i, item in enumerate(raw):
            try:
                case = Case.model_validate(item)
            except ValidationError as e:
                raise ValueError(f"{f.name}[{i}] failed validation:\n{e}") from e
            if case.id in seen_ids:
                raise ValueError(f"{f.name}: duplicate case id {case.id!r}")
            seen_ids.add(case.id)
            # Validate attachment paths eagerly.
            for t in case.turns:
                for att in t.all_attachments():
                    _resolve_attachment(att)
            cases.append(case)

    cases.sort(key=lambda c: c.id)
    return cases


def attachment_bytes(rel: str) -> tuple[str, str, bytes]:
    """Return (filename, content_type, data) for an attachment path."""
    p = _resolve_attachment(rel)
    suffix = p.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        ct = "image/jpeg"
    elif suffix == ".png":
        ct = "image/png"
    elif suffix == ".heic":
        ct = "image/heic"
    elif suffix == ".pdf":
        ct = "application/pdf"
    else:
        ct = "application/octet-stream"
    return p.name, ct, p.read_bytes()
