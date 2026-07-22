"""Configuration for the Klaudia embedding service.

Every field is env-overridable (prefix ``EMBED_``) so one image serves local
dev (mps/cpu), CI (cpu), and a future production inference engine (swap
``EMBED_MODEL`` or point clients at another host). No secrets live here: the
service is unauthenticated and expected to sit on a private network behind the
app.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbedSettings(BaseSettings):
    """Runtime configuration read from ``EMBED_*`` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="EMBED_", extra="ignore", protected_namespaces=()
    )

    model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    device: str = "auto"  # auto | cpu | mps | cuda
    batch_size: int = 32
    normalize: bool = True  # unit vectors: cosine-friendly for pgvector
    host: str = "0.0.0.0"
    port: int = 8100


def get_settings() -> EmbedSettings:
    """Return a fresh settings instance (reads the current environment)."""
    return EmbedSettings()
