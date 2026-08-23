# mcp-archive

FastMCP server for document, page, and extraction metadata. It uses SQLite for
zero-config development and Postgres when `DATABASE_URL` is set.

## Run

```bash
uv sync --active
python main.py --transport stdio   # local subprocess (default)
python main.py --transport http    # stateless service at /mcp; auth required
python main.py --transport sse     # legacy rollback only
```

HTTP bearer auth uses `MCP_JWT_SECRET` with optional `MCP_JWT_ISSUER` and
`MCP_JWT_AUDIENCE` checks. The secret must contain at least 32 characters.
`MCP_ALLOW_INSECURE_HTTP=true` exists only for local smoke tests.

FastMCP is pinned to `4.0.0b3`. Put TLS and rate limits at the gateway. For an
external endpoint, replace the shared HS256 verifier with an asymmetric key and
JWKS.
