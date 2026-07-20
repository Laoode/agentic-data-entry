import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app.server import mcp
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP-Archive Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="Transport mode (default: sse)",
    )
    args = parser.parse_args()

    host = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_PORT", "8001"))

    logger.info(f"Starting MCP-Archive server on {host}:{port} with {args.transport} transport")
    mcp.run(transport=args.transport)
