from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field, model_validator
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

    # LLM (Google Gemini via native google-genai SDK)
    llm_model: str = Field(default="gemini-3-flash-preview", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.5, alias="LLM_TEMPERATURE")
    # Thinking level for Gemini 3 models (gemini-3-*).
    # Valid values: "none", "minimal", "low", "medium", "high" (model default = "high").
    # routing = supervisor router + team_supervisor + _emit_final_reply (classification / summarization)
    # worker  = write_agent, read_agent, sheet_agent, sql_agent (tool-augmented reasoning)
    llm_thinking_level_routing: str = Field(default="minimal", alias="LLM_THINKING_LEVEL_ROUTING")
    llm_thinking_level_worker: str = Field(default="minimal", alias="LLM_THINKING_LEVEL_WORKER")

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

    # OCR / KIE routing
    #
    # KIE (Key Information Extraction) has three execution modes:
    #   mock      → MOCK_KIE=true; return fixture JSON from sample-data/labels/
    #   direct    → OCR_MODE=false; KIE_MODEL handles image -> JSON in one call
    #               (default for now: gemini-3-flash, which is multimodal)
    #   separated → OCR_MODE=true; vLLM GLM-OCR does text recognition only,
    #               then KIE_MODEL extracts JSON from that text. Lets us swap
    #               in the fine-tuned GLM-OCR as KIE_MODEL once training is done.
    vllm_base_url: str = Field(default="", alias="VLLM_BASE_URL")
    auth_token: str = Field(default="", alias="AUTH_TOKEN")
    vllm_ocr_model: str = Field(
        default="zai-org/GLM-OCR", alias="VLLM_OCR_MODEL"
    )
    # MOCK_KIE replaces USE_MOCK_OCR. We keep the old alias as a fallback for
    # one release cycle so existing .env files don't silently break.
    mock_kie: bool = Field(
        default=True, validation_alias="MOCK_KIE"
    )
    # Legacy USE_MOCK_OCR is read for backwards compat; mock_kie wins if both
    # are set. Wired in via @model_validator below.
    legacy_use_mock_ocr: bool | None = Field(default=None, alias="USE_MOCK_OCR")
    ocr_mode: bool = Field(default=False, alias="OCR_MODE")
    kie_model: str = Field(default="gemini-3-flash-preview", alias="KIE_MODEL")
    # Guardrails
    llm_guardrails_prompt_inj: str = Field(
        default="meta-llama/Llama-Prompt-Guard-2-86M",
        alias="LLM_GUARDRAILS_PROMPT_INJ",
    )
    llm_guardrails_model: str = Field(
        default="gemini-3.1-flash-lite-preview", alias="LLM_GUARDRAILS_MODEL"
    )
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")

    # Database
    sqlite_db: str = Field(default="app_dev.db", alias="SQLITE_DB")

    # Redis (hot cache + Taskiq broker + pubsub)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    dedup_cache_ttl_seconds: int = Field(
        default=86400, alias="DEDUP_CACHE_TTL_SECONDS"
    )

    # MinIO (object storage)
    minio_endpoint: str = Field(
        default="http://127.0.0.1:9000", alias="MINIO_ENDPOINT"
    )
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
    ocr_lora_name: str = Field(default="", alias="OCR_LORA_NAME")
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
    # "sse" connects to already-running mcp-sqlite/mcp-gsheets on 8001/8002.
    mcp_transport: str = Field(default="stdio", alias="MCP_TRANSPORT")

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

    @model_validator(mode="after")
    def _coalesce_mock_flag(self) -> "Settings":
        """If a user only set the old USE_MOCK_OCR (and not MOCK_KIE), honor it.

        Strategy: when MOCK_KIE is at its default (True) AND USE_MOCK_OCR is
        explicitly set in env, treat USE_MOCK_OCR as the source of truth. This
        keeps existing .env files working until they're updated.
        """
        if self.legacy_use_mock_ocr is not None:
            self.mock_kie = self.legacy_use_mock_ocr
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
