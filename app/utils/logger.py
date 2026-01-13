"""
Logging configuration for MCP Google Sheets server.
Logs to stderr to maintain protocol integrity (stdout reserved for MCP messages).
"""

import logging
import os
import sys
from typing import Optional


def setup_logger(
    name: str = "mcp-gsheets",
    level: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name identifier
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to env LOG_LEVEL or INFO.
    
    Returns:
        Configured logger instance
    
    Note:
        Logs to stderr to maintain MCP protocol integrity.
        stdout is reserved for JSON-RPC communication.
    """
    log_level = level or os.environ.get("LOG_LEVEL", "INFO")
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create stderr handler (critical for MCP - stdout must be clean)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Format: timestamp - level - module - message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()