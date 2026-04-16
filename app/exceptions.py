class KlaudiaError(Exception):
    """Base exception for Klaudia system."""


class OCRError(KlaudiaError):
    """OCR processing failed."""


class ExtractionError(KlaudiaError):
    """Data extraction failed."""


class GuardrailError(KlaudiaError):
    """Guardrail validation rejected the input."""

    def __init__(self, message: str, reason: str = "rejected"):
        super().__init__(message)
        self.reason = reason


class OrchestrationError(KlaudiaError):
    """Orchestration pipeline failed."""


class LLMError(KlaudiaError):
    """LLM call failed."""


class DatabaseError(KlaudiaError):
    """Database operation failed."""


class MCPConnectionError(KlaudiaError):
    """MCP server connection failed."""
