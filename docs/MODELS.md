# Model Providers — Agentic LLM Guide

How the supervisor + sub-agents pick a chat backend, and what differs per
provider. Guardrails and KIE/OCR are **not** covered by this switch — they stay
Gemini-native regardless of `MODEL_PROVIDER`.

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

### Caveat — thinking + tool calls

With thinking **enabled**, DeepSeek returns `reasoning_content` alongside
`content`, and on tool-call turns that `reasoning_content` must be passed back or
the API returns 400. The current react workers (langchain-openai) don't
round-trip it, so keep `LLM_DISABLE_THINKING=true` for `deepseek`. Enabling
thinking for the tool-calling workers is an open item (see MEMORY.md O8/O9).
