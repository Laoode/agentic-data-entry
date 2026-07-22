"""OpenAI-compatible embedding HTTP service.

Exposes ``POST /v1/embeddings`` so the mem0 ``openai`` embedder can call it with
a custom base_url. Keeping the OpenAI contract is deliberate: local dev, CI, and
the future production inference engine all speak the same protocol, so swapping
the backend is a URL change, not a code change.
"""

from __future__ import annotations

import base64
import struct
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from embed.encoder import Encoder, SentenceTransformerEncoder
from embed.models import (
    EmbeddingData,
    EmbeddingRequest,
    EmbeddingResponse,
    HealthResponse,
    Usage,
)
from embed.settings import EmbedSettings, get_settings


def _encode_base64(vector: list[float]) -> str:
    """Pack a float vector as little-endian float32 base64 (OpenAI wire format)."""
    packed = struct.pack(f"<{len(vector)}f", *vector)
    return base64.b64encode(packed).decode("ascii")


def _estimate_tokens(texts: list[str]) -> int:
    """Rough token estimate for the usage field (advisory only)."""
    return sum(len(text.split()) for text in texts)


def create_app(
    encoder: Encoder | None = None, settings: EmbedSettings | None = None
) -> FastAPI:
    """Build the FastAPI app.

    Args:
        encoder: Pre-built encoder to use (tests inject a fake). When None, the
            lifespan loads a ``SentenceTransformerEncoder`` from settings on
            startup so importing this module never loads a model.
        settings: Config override; defaults to the environment.

    Returns:
        A configured FastAPI application.
    """
    cfg = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "encoder", None) is None:
            app.state.encoder = SentenceTransformerEncoder(
                model_name=cfg.model,
                device=cfg.device,
                batch_size=cfg.batch_size,
                normalize=cfg.normalize,
            )
        yield

    app = FastAPI(title="Klaudia Embedding Service", lifespan=lifespan)
    if encoder is not None:
        app.state.encoder = encoder

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        enc: Encoder = app.state.encoder
        return HealthResponse(
            status="ok",
            model=enc.model_name,
            device=enc.device,
            dimensions=enc.dimensions,
        )

    @app.post("/v1/embeddings", response_model=EmbeddingResponse)
    async def embeddings(req: EmbeddingRequest) -> EmbeddingResponse:
        enc: Encoder = app.state.encoder
        texts = req.texts()
        if not texts:
            raise HTTPException(status_code=400, detail="input must not be empty")
        vectors = enc.encode(texts)
        data: list[EmbeddingData] = []
        for i, vector in enumerate(vectors):
            value = (
                _encode_base64(vector) if req.encoding_format == "base64" else vector
            )
            data.append(EmbeddingData(index=i, embedding=value))
        tokens = _estimate_tokens(texts)
        return EmbeddingResponse(
            data=data,
            model=req.model or enc.model_name,
            usage=Usage(prompt_tokens=tokens, total_tokens=tokens),
        )

    return app


app = create_app()
