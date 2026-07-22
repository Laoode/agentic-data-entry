"""Test fixtures for the embedding service.

The ``FakeEncoder`` is deterministic and dependency-free so the HTTP contract is
tested without importing torch. The real model is exercised separately in
``test_encoder_real.py`` (opt-in).
"""

import hashlib

import pytest
from fastapi.testclient import TestClient

from embed.app import create_app


class FakeEncoder:
    """Deterministic encoder: hashes text into a fixed-dim pseudo-vector."""

    def __init__(self, dimensions: int = 8) -> None:
        self._dims = dimensions

    @property
    def model_name(self) -> str:
        return "fake-encoder"

    @property
    def device(self) -> str:
        return "cpu"

    @property
    def dimensions(self) -> int:
        return self._dims

    def encode(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vector = [
                (digest[i % len(digest)] / 255.0) * 2 - 1 for i in range(self._dims)
            ]
            out.append(vector)
        return out


@pytest.fixture
def encoder() -> FakeEncoder:
    return FakeEncoder(dimensions=8)


@pytest.fixture
def client(encoder: FakeEncoder):
    with TestClient(create_app(encoder=encoder)) as test_client:
        yield test_client
