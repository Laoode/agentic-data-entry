import argparse
import os

from dotenv import load_dotenv

load_dotenv()

from ledger.server import mcp  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP-Ledger Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    args = parser.parse_args()

    host = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_PORT", "8003"))
    mcp.run(transport=args.transport)
