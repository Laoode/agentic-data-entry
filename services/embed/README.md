# Klaudia Embedding Service

An isolated, OpenAI-compatible embedding endpoint. It is the mem0 embedder
backend for Klaudia's long-term memory (see `docs/PLAN.md`, Part 2).

## Why it is standalone (not a uv-workspace member)

The model runtime (`torch` via `sentence-transformers`) is heavy and must not
leak into the app's virtualenv. The service is reached only over HTTP and is
meant to be replaced by the production inference engine later: when that day
comes, point mem0's `base_url` at the new host and delete this folder. Nothing
in the app or mem0 config changes.

## Interface

OpenAI-compatible, so mem0's `openai` embedder consumes it unchanged:

```
POST /v1/embeddings   {"input": "text" | ["a","b"], "encoding_format": "float"|"base64"}
  -> {"object":"list","data":[{"object":"embedding","index":0,"embedding":[...]}],
      "model":"...","usage":{"prompt_tokens":N,"total_tokens":N}}

GET  /health          -> {"status":"ok","model":"...","device":"...","dimensions":384}
```

`base64` returns little-endian float32 (what the OpenAI Python client requests
by default), so the mem0 -> openai-client -> this-service path round-trips.

## Config (env, prefix `EMBED_`)

| Var | Default | Note |
|-----|---------|------|
| `EMBED_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | swappable; dims follow the model |
| `EMBED_DEVICE` | `auto` | `auto` prefers mps, then cuda, then cpu; force `cpu` in CI |
| `EMBED_BATCH_SIZE` | `32` | |
| `EMBED_NORMALIZE` | `true` | L2-normalize (cosine-friendly for pgvector) |
| `EMBED_HOST` / `EMBED_PORT` | `0.0.0.0` / `8100` | |

## Run

```bash
# real serving needs the model extra (pulls torch)
uv pip install 'klaudia-embed[model]'
uv run --project services/embed python -m embed
```

## Test

```bash
# hermetic HTTP-contract tests (fake encoder, no torch)
uv run pytest services/embed/tests -q

# opt-in real-model smoke (downloads weights)
EMBED_REAL_TEST=1 uv run --project services/embed \
    pytest services/embed/tests/test_encoder_real.py -q
```
