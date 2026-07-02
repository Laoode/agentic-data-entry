# Model Providers — Agentic LLM Guide

How the supervisor + sub-agents pick a chat backend, and what differs per
provider. Guardrails and KIE/OCR are **not** covered by this switch (they ignore
`MODEL_PROVIDER`). KIE stays Gemini/vLLM per `KIE_MODEL`; guardrails have their
own independent `GUARDRAILS_PROVIDER` switch (see below).

## The one seam

Everything routes through `klaudia/core/supervisor/llm.py::build_chat_llm()`.
The rest of the graph (router, team supervisor, react workers) is
provider-agnostic. Add a provider by extending that file + `config/settings.py`;
nothing else changes.

```
container.py
  └─ settings.active_openai_endpoint()   # resolves (base_url, api_key) per provider
  └─ SupervisorAgent(provider=..., ...)
       └─ build_chat_llm(provider=...)    # picks Gemini vs OpenAI-compatible
```

## Switching providers

Edit two lines in `.env`, then restart:

| Provider   | MODEL_PROVIDER | LLM_MODEL (example)   | Credentials used                     |
|------------|----------------|-----------------------|--------------------------------------|
| Gemini     | `google`       | `gemini-3-flash-preview` | `LLM_API_KEY` or Vertex AI vars   |
| Qwen/vLLM  | `vllm`         | `Qwen/Qwen3.5-27B`    | `VLLM_LLM_ENDPOINT` + `VLLM_LLM_API_KEY` |
| DeepSeek   | `deepseek`     | `deepseek-v4-pro`     | `DEEPSEEK_BASE_URL` + `DEEPSEEK_API_KEY` |

Each provider keeps its own credentials in `.env`, so flipping back and forth
never requires re-pasting endpoints/keys. `openai` is accepted as a legacy alias
for `vllm`.

## Thinking-mode mechanics (the per-provider difference)

All three are "OpenAI-compatible" on the wire, but reasoning is toggled
differently. `LLM_DISABLE_THINKING=true` maps to:

| Provider | Mechanism                                                        |
|----------|------------------------------------------------------------------|
| Gemini   | `generation_config.thinking_config.thinking_level` (`LLM_THINKING_LEVEL_*`) |
| vLLM/Qwen| `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` (in-code `/no_think`) |
| DeepSeek | `extra_body={"thinking": {"type": "disabled"}}`                  |

`_openai_thinking_extra_body()` resolves the vLLM/DeepSeek case. Gemini uses
`thinking_level` bound on the model.

## Structured output

`with_structured(llm, schema)` is provider-aware:

- **Gemini** — native structured output.
- **DeepSeek** — `method="function_calling"` (its reliable tool path; strict
  `json_schema` is beta-only).
- **vLLM/Qwen** — `method="json_schema"` so the constraint rides on guided
  decoding even when the server lacks `--enable-auto-tool-choice`.

## DeepSeek V4 specifics

Base URL `https://api.deepseek.com/v1` (`/beta` for prefix completion). Verified
against the official docs:

- **Thinking** — defaults to enabled; we disable it for the agentic stack (see
  caveat below). Toggle is `extra_body`, not the model name.
- **Tool calls** — standard OpenAI format, supported from V3.2+. Strict mode
  (`"strict": true`) needs the `/beta` endpoint and drops `minLength`/`maxLength`
  and `minItems`/`maxItems`.
- **Multi-round** — stateless; you append the full history each turn (LangGraph
  already does this).
- **KV cache** — automatic disk caching, no config. Usage reports
  `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`. Keeping a stable system
  prompt prefix maximizes hits.
- **Prefix completion** — `/beta` endpoint; last message `{"role":"assistant",
  "content": "...", "prefix": true}`. Not wired into the agentic graph.

## Guardrails provider

The guardrail LLM checks (scope: SARA / Financial Advice, plus the output
blacklist) route through `app/services/guardrails/llm.py::GuardrailsLLMRouter`,
selected by `GUARDRAILS_PROVIDER` — independent of `MODEL_PROVIDER`. The
prompt-injection guard always stays on Groq (`guardrails/base.py`).

| `GUARDRAILS_PROVIDER` | Backend                         | `LLM_GUARDRAILS_MODEL` example | Thinking off via                     |
|-----------------------|---------------------------------|--------------------------------|--------------------------------------|
| `google` (default)    | Gemini (shared `LLMClient`)     | `gemini-3.1-flash-lite`        | `thinking_level="minimal"` (bound in `LLMClient`) |
| `deepseek`            | DeepSeek V4 (OpenAI-compatible) | `deepseek-v4-flash`            | `extra_body={"thinking": {"type": "disabled"}}`   |

DeepSeek reuses `DEEPSEEK_BASE_URL` / `DEEPSEEK_API_KEY`. Both backends run
non-thinking; the mechanism differs (same split as the agentic stack above). The
router owns the DeepSeek client's lifecycle and closes it on container shutdown;
the Gemini client is shared and owned by the container.

## KIE / receipt extraction

KIE is independent of `MODEL_PROVIDER` (that switch is only the agentic stack).
The extraction backend is chosen from `KIE_MODEL` alone — no mode flag:

| Condition                       | Backend          | Prompt                                  |
|---------------------------------|------------------|-----------------------------------------|
| `MOCK_KIE=true`                 | fixture lookup   | none (offline, `sample-data/labels/`)   |
| `KIE_MODEL` starts with `gemini`| `GeminiKIEClient`| full zero-shot (`agents/prompt.py`)     |
| `KIE_MODEL` anything else       | `VLLMKIEClient`  | none — image-only                       |

`KIEClient.extract_from_image()` is the only seam IngestService + Taskiq workers
call; it routes internally via `_is_gemini_model()`.

- **Gemini path** — a general multimodal model, so it needs the schema + rules +
  few-shot prompt to extract zero-shot.
- **vLLM path** — a Qwen3.5-4B fine-tuned for receipt→JSON, served on vLLM. Its
  chat template (`template.jinja`) injects the same short prompt used in
  training, so the client sends the **image only**. To switch to it, set
  `KIE_MODEL` to the served model name + fill `VLLM_KIE_ENDPOINT`
  (full `/v1/chat/completions` URL) and `VLLM_KIE_API_KEY`.

Provenance (`ocr_model`, `schema_version`) is persisted per page to
`blob_extraction` so extractions can be re-run when the model is upgraded.

### Caveat — thinking + tool calls

With thinking **enabled**, DeepSeek returns `reasoning_content` alongside
`content`, and on tool-call turns that `reasoning_content` must be passed back or
the API returns 400. The current react workers (langchain-openai) don't
round-trip it, so keep `LLM_DISABLE_THINKING=true` for `deepseek`. Enabling
thinking for the tool-calling workers is an open item (see MEMORY.md O8/O9).
