#!/bin/bash
set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Installing all dependencies (workspace)...${NC}"
uv sync
echo -e "${GREEN}All dependencies installed.${NC}"
