"""Klaudia embedding service.

A standalone, OpenAI-compatible embedding endpoint used as the mem0 embedder
backend. Deliberately NOT a uv-workspace member: its model runtime (torch via
sentence-transformers) must not leak into the app venv, and the whole service is
meant to be replaced by the production inference engine later (repoint one URL).
"""

__version__ = "0.1.0"
