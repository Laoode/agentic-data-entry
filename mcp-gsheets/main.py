#  Server Start#!/usr/bin/env python
"""
MCP Google Sheets Server - Entry Point.
Run with: uv run python main.py [--transport stdio|sse]
"""

from app import main

if __name__ == "__main__":
    main()