"""Embedding backend, isolated behind a small ``Encoder`` Protocol.

The HTTP layer depends only on ``Encoder``, so tests inject a fake and never
import torch. The real implementation loads sentence-transformers lazily, which
is why ``sentence-transformers`` stays an optional dependency (the ``model``
extra). This is also the seam that makes the model swappable: change
``EMBED_MODEL`` and the dimensions follow from the loaded model, no code edit.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Encoder(Protocol):
    """Minimal contract the HTTP layer needs from an embedding backend."""

    @property
    def model_name(self) -> str: ...

    @property
    def device(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    def encode(self, texts: list[str]) -> list[list[float]]: ...


def resolve_device(preference: str) -> str:
    """Resolve a torch device string.

    Args:
        preference: ``auto``, ``cpu``, ``mps``, or ``cuda``. ``auto`` prefers
            mps (Apple Silicon), then cuda, then cpu.

    Returns:
        The concrete device string to hand to sentence-transformers.
    """
    if preference != "auto":
        return preference
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class SentenceTransformerEncoder:
    """Encoder backed by a sentence-transformers model."""

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        batch_size: int = 32,
        normalize: bool = True,
    ) -> None:
        """Load the model onto the resolved device.

        Args:
            model_name: HuggingFace/sentence-transformers model id.
            device: Device preference (see ``resolve_device``).
            batch_size: Batch size passed to ``encode``.
            normalize: L2-normalize outputs (cosine-friendly for pgvector).

        Raises:
            RuntimeError: If sentence-transformers is not installed.
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install the model extra: "
                "uv pip install 'klaudia-embed[model]'"
            ) from exc
        self._model_name = model_name
        self._device = resolve_device(device)
        self._batch_size = batch_size
        self._normalize = normalize
        self._model = SentenceTransformer(model_name, device=self._device)
        self._dims = int(self._model.get_sentence_embedding_dimension())

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def device(self) -> str:
        return self._device

    @property
    def dimensions(self) -> int:
        return self._dims

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into a list of float vectors."""
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=self._normalize,
            convert_to_numpy=True,
        )
        return vectors.tolist()
