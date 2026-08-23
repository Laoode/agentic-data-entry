import os

from app.server import mcp
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def _enabled(name: str) -> bool:
    """Return whether an environment flag is enabled.

    Args:
        name: Environment variable name.

    Returns:
        True for 1, true, yes, or on, ignoring case.
    """
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def run_server(transport: str) -> None:
    """Run the archive server on the selected transport.

    Args:
        transport: One of stdio, http, or legacy sse.

    Raises:
        RuntimeError: If HTTP starts without auth or an explicit dev override.
    """
    if transport == "stdio":
        mcp.run(transport="stdio")
        return

    host = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_PORT", "8001"))
    if (
        transport == "http"
        and not os.getenv("MCP_JWT_SECRET")
        and not _enabled("MCP_ALLOW_INSECURE_HTTP")
    ):
        raise RuntimeError(
            "HTTP transport requires MCP_JWT_SECRET; set "
            "MCP_ALLOW_INSECURE_HTTP=true only for local development"
        )

    kwargs = {
        "host": host,
        "port": port,
        "host_origin_protection": "auto",
    }
    if transport == "http":
        kwargs["stateless_http"] = True
    mcp.run(transport=transport, **kwargs)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP-Archive Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport mode; sse is legacy (default: stdio)",
    )
    args = parser.parse_args()

    logger.info("Starting MCP-Archive with %s transport", args.transport)
    run_server(args.transport)
