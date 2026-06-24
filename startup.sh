#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

FASTAPI_PORT=${PORT:-8000}
MCP_SQLITE_PORT=8001
MCP_GSHEETS_PORT=8002
MINIO_API_PORT=${MINIO_API_PORT:-9000}
MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT:-9001}
MINIO_DATA_DIR=${MINIO_DATA_DIR:-"$HOME/codex/minio/data"}

MCP_TRANSPORT=${MCP_TRANSPORT:-stdio}

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"

mkdir -p "$PROJECT_DIR/logs"

echo -e "${GREEN}Starting Klaudia services (MCP_TRANSPORT=$MCP_TRANSPORT)...${NC}"

# Start MinIO
echo -e "${YELLOW}Starting MinIO (data: $MINIO_DATA_DIR)...${NC}"
minio server "$MINIO_DATA_DIR" \
  --address ":$MINIO_API_PORT" \
  --console-address ":$MINIO_CONSOLE_PORT" \
  > "$PROJECT_DIR/logs/minio.log" 2>&1 &
echo $! > "$PROJECT_DIR/logs/minio.pid"
echo -e "${GREEN}MinIO started (PID: $(cat "$PROJECT_DIR/logs/minio.pid"))${NC}"
echo -e "${YELLOW}Waiting for MinIO to start...${NC}"
sleep 2

if [ "$MCP_TRANSPORT" = "sse" ]; then
  # Start MCP-SQLite
  echo -e "${YELLOW}Starting MCP-SQLite on port $MCP_SQLITE_PORT...${NC}"
  cd "$PROJECT_DIR/mcp-sqlite"
  FASTMCP_PORT=$MCP_SQLITE_PORT SQLITE_DB="$PROJECT_DIR/app_dev.db" \
    "$PYTHON" main.py --transport sse > "$PROJECT_DIR/logs/mcp-sqlite.log" 2>&1 &
  echo $! > "$PROJECT_DIR/logs/mcp-sqlite.pid"
  echo -e "${GREEN}MCP-SQLite started (PID: $(cat "$PROJECT_DIR/logs/mcp-sqlite.pid"))${NC}"

  # Start MCP-GSheets
  echo -e "${YELLOW}Starting MCP-GSheets on port $MCP_GSHEETS_PORT...${NC}"
  cd "$PROJECT_DIR/mcp-gsheets"
  FASTMCP_PORT=$MCP_GSHEETS_PORT \
    "$PYTHON" main.py --transport sse > "$PROJECT_DIR/logs/mcp-gsheets.log" 2>&1 &
  echo $! > "$PROJECT_DIR/logs/mcp-gsheets.pid"
  echo -e "${GREEN}MCP-GSheets started (PID: $(cat "$PROJECT_DIR/logs/mcp-gsheets.pid"))${NC}"

  echo -e "${YELLOW}Waiting for MCP servers to start...${NC}"
  sleep 3
else
  echo -e "${YELLOW}stdio mode: MCP servers will be spawned by FastAPI as subprocesses.${NC}"
fi

# Start FastAPI
echo -e "${YELLOW}Starting FastAPI on port $FASTAPI_PORT...${NC}"
cd "$PROJECT_DIR"
MCP_TRANSPORT=$MCP_TRANSPORT \
  "$PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port $FASTAPI_PORT \
  > "$PROJECT_DIR/logs/fastapi.log" 2>&1 &
echo $! > "$PROJECT_DIR/logs/fastapi.pid"
echo -e "${GREEN}FastAPI started (PID: $(cat "$PROJECT_DIR/logs/fastapi.pid"))${NC}"

echo -e "${GREEN}All services started.${NC}"
echo -e "  FastAPI:     http://localhost:$FASTAPI_PORT"
echo -e "  MinIO API:   http://localhost:$MINIO_API_PORT"
echo -e "  MinIO UI:    http://localhost:$MINIO_CONSOLE_PORT"
if [ "$MCP_TRANSPORT" = "sse" ]; then
  echo -e "  MCP-SQLite:  http://localhost:$MCP_SQLITE_PORT"
  echo -e "  MCP-GSheets: http://localhost:$MCP_GSHEETS_PORT"
fi