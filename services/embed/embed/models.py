"""OpenAI-compatible request/response schemas for the embedding endpoint.

The wire shape mirrors ``POST /v1/embeddings`` from the OpenAI API so the mem0
``openai`` embedder can call this service unchanged via a custom base_url.
"""

from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, field_validator


class EmbeddingRequest(BaseModel):
    """Body of ``POST /v1/embeddings``.

    ``input`` is a single string or a list of strings. ``encoding_format``
    follows OpenAI: ``float`` returns raw float lists, ``base64`` returns
    little-endian float32 packed as base64 (what the OpenAI Python client asks
    for by default).
    """

    model_config = ConfigDict(protected_namespaces=())

    input: Union[str, list[str]]
    model: str | None = None
    encoding_format: Literal["float", "base64"] = "float"

    @field_validator("input")
    @classmethod
    def _non_empty(cls, value: Union[str, list[str]]) -> Union[str, list[str]]:
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("input string must not be empty")
            return value
        if not value:
            raise ValueError("input list must not be empty")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("input list items must be non-empty strings")
        return value

    def texts(self) -> list[str]:
        """Normalize ``input`` to a list of strings."""
        return [self.input] if isinstance(self.input, str) else list(self.input)


class EmbeddingData(BaseModel):
    """One embedding in the response ``data`` array."""

    object: str = "embedding"
    index: int
    embedding: Union[list[float], str]


class Usage(BaseModel):
    """Approximate token accounting (advisory; clients rarely depend on it)."""

    prompt_tokens: int
    total_tokens: int


class EmbeddingResponse(BaseModel):
    """Full ``POST /v1/embeddings`` response envelope."""

    model_config = ConfigDict(protected_namespaces=())

    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: Usage


class HealthResponse(BaseModel):
    """Body of ``GET /health``: what model is loaded and where."""

    model_config = ConfigDict(protected_namespaces=())

    status: str
    model: str
    device: str
    dimensions: int
