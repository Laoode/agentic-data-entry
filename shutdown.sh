#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FASTAPI_PORT=${PORT:-8000}
MCP_SQLITE_PORT=8001
MCP_GSHEETS_PORT=8002

echo -e "${YELLOW}Stopping Klaudia services...${NC}"

for service in fastapi mcp-sqlite mcp-gsheets; do
    pidfile="logs/$service.pid"
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo -e "${GREEN}Stopped $service (PID: $pid)${NC}"
        else
            echo -e "${YELLOW}$service already stopped${NC}"
        fi
        rm -f "$pidfile"
    else
        echo -e "${YELLOW}No PID file for $service${NC}"
    fi
done

echo -e "${GREEN}All services stopped.${NC}"
