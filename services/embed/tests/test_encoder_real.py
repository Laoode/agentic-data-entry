"""Opt-in smoke test against the real multilingual model.

Skipped unless ``EMBED_REAL_TEST=1`` so CI and local runs do not download the
model weights by accident. Run explicitly with:

    EMBED_REAL_TEST=1 uv run --project services/embed pytest \
        services/embed/tests/test_encoder_real.py
"""

import math
import os

import pytest

pytestmark = pytest.mark.real_model

_RUN = os.environ.get("EMBED_REAL_TEST") == "1"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb)


@pytest.mark.skipif(not _RUN, reason="set EMBED_REAL_TEST=1 to load the real model")
def test_real_model_dims_and_cross_lingual_similarity():
    from embed.encoder import SentenceTransformerEncoder

    encoder = SentenceTransformerEncoder(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        device="cpu",
    )
    assert encoder.dimensions == 384

    vectors = encoder.encode(["kucing duduk di atas meja", "a cat sits on the table"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    # ID and EN paraphrases of the same sentence should be clearly related.
    assert _cosine(vectors[0], vectors[1]) > 0.5
