class MCPSQLiteError(Exception):
    """Base exception for MCP-Archive server."""


class DocumentNotFoundError(MCPSQLiteError):
    """Requested document does not exist."""


class PageNotFoundError(MCPSQLiteError):
    """Requested page does not exist."""
