from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Service
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    service_name: str = Field(default="Klaudia Chatbot", alias="SERVICE_NAME")
    version: str = Field(default="1.0.0", alias="VERSION")
    debug: bool = Field(default=True, alias="DEBUG")
    stage: str = Field(default="development", alias="STAGE")

    # Auth (self-issued JWT). The dev default secret is refused when
    # STAGE=production — see validate_production_secrets().
    jwt_secret: str = Field(
        default="dev-secret-change-me-before-any-deploy", alias="JWT_SECRET"
    )
    jwt_expires_days: int = Field(default=7, alias="JWT_EXPIRES_DAYS")

    # Edge rate limits (slowapi syntax, e.g. "10/minute"). Auth is keyed by
    # client IP, chat by authenticated user id. Per-node in-memory windows.
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_auth: str = Field(default="10/minute", alias="RATE_LIMIT_AUTH")
    rate_limit_chat: str = Field(default="30/minute", alias="RATE_LIMIT_CHAT")

    # Agentic LLM provider (supervisor + sub-agents). Guardrails + KIE stay on
    # Gemini regardless. Values: "google" | "vllm" | "deepseek". See docs/MODELS.md.
    model_provider: str = Field(default="google", alias="MODEL_PROVIDER")
    # Force reasoning off on the agentic stack. Applies to vllm/deepseek only;
    # the per-provider extra_body is resolved in klaudia/core/supervisor/llm.py.
    llm_disable_thinking: bool = Field(default=True, alias="LLM_DISABLE_THINKING")

    # OpenAI-compatible credentials, kept per provider so switching MODEL_PROVIDER
    # never requires re-pasting endpoints/keys. Resolved via active_openai_endpoint().
    # NOTE: distinct from the KIE vLLM server below (VLLM_KIE_ENDPOINT).
    vllm_llm_endpoint: str = Field(default="", alias="VLLM_LLM_ENDPOINT")
    vllm_llm_api_key: str = Field(default="", alias="VLLM_LLM_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")

    # LLM (Google Gemini via native google-genai SDK)
    llm_model: str = Field(default="gemini-3-flash-preview", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.5, alias="LLM_TEMPERATURE")
    # Thinking level for Gemini 3 models (gemini-3-*).
    # Valid values: "minimal", "low", "medium", "high" (model default = "high").
    # routing = supervisor router + team_supervisor + _emit_final_reply (classification / summarization)
    # worker  = write_agent, read_agent, sheet_agent, sql_agent (tool-augmented reasoning)
    llm_thinking_level_routing: str = Field(
        default="minimal", alias="LLM_THINKING_LEVEL_ROUTING"
    )
    llm_thinking_level_worker: str = Field(
        default="minimal", alias="LLM_THINKING_LEVEL_WORKER"
    )

    # Vertex AI (when google_genai_use_vertexai=True, all Gemini calls route
    # through GCP Vertex AI instead of the Gemini Developer API. ADC is read
    # from google_application_credentials).
    google_cloud_project: str = Field(default="", alias="GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str = Field(default="global", alias="GOOGLE_CLOUD_LOCATION")
    google_genai_use_vertexai: bool = Field(
        default=False, alias="GOOGLE_GENAI_USE_VERTEXAI"
    )
    google_application_credentials: str = Field(
        default="", alias="GOOGLE_APPLICATION_CREDENTIALS"
    )

    # KIE (Key Information Extraction) routing — backend derived from KIE_MODEL:
    #   MOCK_KIE=true             → fixture JSON from sample-data/labels/ (offline)
    #   KIE_MODEL startswith gemini → Gemini SDK, full zero-shot prompt (image→JSON)
    #   KIE_MODEL anything else     → fine-tuned model on vLLM (image-only)
    # See docs/MODELS.md.
    kie_model: str = Field(default="gemini-3-flash-preview", alias="KIE_MODEL")
    # vLLM KIE endpoint (full /v1/chat/completions URL) for the fine-tuned model.
    # Distinct from the agentic vLLM server (VLLM_LLM_ENDPOINT).
    vllm_kie_endpoint: str = Field(default="", alias="VLLM_KIE_ENDPOINT")
    vllm_kie_api_key: str = Field(default="", alias="VLLM_KIE_API_KEY")
    # Offline fixture mode for KIE (sample-data/labels/).
    mock_kie: bool = Field(default=True, alias="MOCK_KIE")
    # Deterministic numeric verification of replies (anti-hallucination).
    # "off" | "log" (flag ungrounded amounts, ship anyway) | "enforce"
    # (one grounded-rewrite retry; original ships if the rewrite still
    # fails). Default "log" until the false-positive rate is measured.
    numeric_verify_mode: str = Field(default="log", alias="NUMERIC_VERIFY_MODE")

    # Guardrails
    guardrails_enabled: bool = Field(default=True, alias="GUARDRAILS_ENABLED")
    llm_guardrails_prompt_inj: str = Field(
        default="meta-llama/Llama-Prompt-Guard-2-86M",
        alias="LLM_GUARDRAILS_PROMPT_INJ",
    )
    # Backend for the scope (SARA / Financial Advice) + output blacklist checks.
    # Independent of MODEL_PROVIDER. "google" (Gemini, default) or "deepseek".
    # DeepSeek reuses DEEPSEEK_BASE_URL / DEEPSEEK_API_KEY. Prompt-injection stays
    # on Groq regardless. See docs/MODELS.md.
    guardrails_provider: str = Field(default="google", alias="GUARDRAILS_PROVIDER")
    llm_guardrails_model: str = Field(
        default="gemini-3.1-flash-lite-preview", alias="LLM_GUARDRAILS_MODEL"
    )
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")

    # Database
    sqlite_db: str = Field(default="app_dev.db", alias="SQLITE_DB")
    # Postgres DSN (postgresql://user:pass@host:5432/db). When set, the app
    # data layer uses PgDBClient instead of SQLite. Leave empty until the MCP
    # SQL-tool server is ported too — see db_client_pg.py module docstring.
    database_url: str = Field(default="", alias="DATABASE_URL")

    # Memory (mem0 OSS long-term memory). Self-hosted: pgvector on the same
    # Postgres, DeepSeek for fact extraction (reuses DEEPSEEK_*), and our
    # isolated embedding service (services/embed) as the embedder. Off by
    # default; promote off -> read -> write like NUMERIC_VERIFY_MODE.
    memory_mode: str = Field(default="off", alias="MEMORY_MODE")  # off|read|write
    # How a memory write runs once MEMORY_MODE=write. "inline" runs mem0.add in
    # an app background task (no worker needed; good for dev/CI/single-node).
    # "taskiq" enqueues to a Taskiq worker (durable across restarts, offloaded,
    # retryable) — needs a running worker or writes queue unprocessed. Mirrors
    # EXTRACTION_MODE=sync|async.
    memory_write_mode: str = Field(default="inline", alias="MEMORY_WRITE_MODE")
    memory_top_k: int = Field(default=6, alias="MEMORY_TOP_K")
    memory_collection: str = Field(default="klaudia_memory", alias="MEMORY_COLLECTION")
    memory_llm_model: str = Field(default="deepseek-v4-flash", alias="MEMORY_LLM_MODEL")
    memory_embed_base_url: str = Field(
        default="http://localhost:8100/v1", alias="MEMORY_EMBED_BASE_URL"
    )
    memory_embed_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2", alias="MEMORY_EMBED_MODEL"
    )
    memory_embed_dims: int = Field(default=384, alias="MEMORY_EMBED_DIMS")

    # Redis (hot cache + Taskiq broker + pubsub)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    dedup_cache_ttl_seconds: int = Field(default=86400, alias="DEDUP_CACHE_TTL_SECONDS")

    # MinIO (object storage)
    minio_endpoint: str = Field(default="http://127.0.0.1:9000", alias="MINIO_ENDPOINT")
    minio_region: str = Field(default="us-east-1", alias="MINIO_REGION")
    minio_access_key: str = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="klaudia-blobs", alias="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, alias="MINIO_SECURE")

    # Taskiq
    taskiq_broker_url: str = Field(
        default="redis://localhost:6379/1", alias="TASKIQ_BROKER_URL"
    )
    taskiq_result_backend_url: str = Field(
        default="redis://localhost:6379/2", alias="TASKIQ_RESULT_BACKEND_URL"
    )
    taskiq_queue_name: str = Field(default="ocr:extract", alias="TASKIQ_QUEUE_NAME")
    taskiq_result_ttl_seconds: int = Field(
        default=3600, alias="TASKIQ_RESULT_TTL_SECONDS"
    )

    # Extraction limits / pressure relief
    max_image_bytes: int = Field(default=10 * 1024 * 1024, alias="MAX_IMAGE_BYTES")
    max_pdf_bytes: int = Field(default=50 * 1024 * 1024, alias="MAX_PDF_BYTES")
    max_pdf_pages: int = Field(default=50, alias="MAX_PDF_PAGES")
    max_images_per_upload: int = Field(default=5, alias="MAX_IMAGES_PER_UPLOAD")
    extraction_queue_depth_warn: int = Field(
        default=50, alias="EXTRACTION_QUEUE_DEPTH_WARN"
    )
    extraction_queue_depth_reject: int = Field(
        default=200, alias="EXTRACTION_QUEUE_DEPTH_REJECT"
    )
    ocr_schema_version: str = Field(default="v1", alias="OCR_SCHEMA_VERSION")

    # Extraction execution mode:
    #   "sync"  — orchestrator awaits OCR inline (legacy + simple dev mode)
    #   "async" — orchestrator enqueues to Taskiq workers and subscribes via
    #             Redis pubsub for per-page completion events. Production.
    extraction_mode: str = Field(default="sync", alias="EXTRACTION_MODE")
    # Per-task timeout (s) after the orchestrator stops waiting for a page.
    extraction_page_timeout_seconds: int = Field(
        default=120, alias="EXTRACTION_PAGE_TIMEOUT_SECONDS"
    )

    # MCP transport: "stdio" spawns servers as subprocesses (no idle SSE drop);
    # "sse" connects to already-running mcp-archive/mcp-gsheets on 8001/8002.
    mcp_transport: str = Field(default="stdio", alias="MCP_TRANSPORT")

    # Sheets tool backend: "gsheets" (Google Sheets API) or "ledger"
    # (Postgres-backed mcp-ledger, identical tool surface; needs DATABASE_URL).
    sheets_backend: str = Field(default="gsheets", alias="SHEETS_BACKEND")

    # Langfuse Observability
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_base_url: str = Field(
        default="https://cloud.langfuse.com", alias="LANGFUSE_BASE_URL"
    )
    langfuse_enabled: bool = Field(default=True, alias="LANGFUSE_ENABLED")

    # Logging
    log_path: str = Field(default="logs", alias="LOG_PATH")

    model_config = {"env_file": ".env", "extra": "ignore"}

    def active_openai_endpoint(self) -> tuple[str, str]:
        """Return (base_url, api_key) for the active OpenAI-compatible provider.

        Only meaningful when model_provider is "vllm" or "deepseek".
        """
        if self.model_provider.strip().lower() in ("deepseek",):
            return self.deepseek_base_url, self.deepseek_api_key
        return self.vllm_llm_endpoint, self.vllm_llm_api_key

    def validate_production_secrets(self) -> None:
        """Fail fast on insecure production configuration.

        Called once at app startup (main.py lifespan), not in the model
        validator, so tests can freely construct Settings(stage="production").

        Raises:
            ValueError: If STAGE=production still uses the dev JWT secret.
        """
        if (
            self.stage == "production"
            and self.jwt_secret == "dev-secret-change-me-before-any-deploy"
        ):
            raise ValueError(
                "JWT_SECRET must be set to a strong random value when "
                "STAGE=production (dev default refused)."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
