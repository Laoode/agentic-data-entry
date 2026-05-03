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

    # LLM (Google Gemini via native google-genai SDK)
    llm_model: str = Field(default="gemini-3-flash-preview", alias="LLM_MODEL")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.5, alias="LLM_TEMPERATURE")

    # OCR (vLLM - GLM-OCR direct JSON extraction)
    vllm_base_url: str = Field(default="", alias="VLLM_BASE_URL")
    auth_token: str = Field(default="", alias="AUTH_TOKEN")
    vllm_ocr_model: str = Field(
        default="zai-org/GLM-OCR", alias="VLLM_OCR_MODEL"
    )
    use_mock_ocr: bool = Field(default=True, alias="USE_MOCK_OCR")
    # Guardrails
    llm_guardrails_prompt_inj: str = Field(
        default="meta-llama/Llama-Prompt-Guard-2-86M",
        alias="LLM_GUARDRAILS_PROMPT_INJ",
    )
    llm_guardrails_model: str = Field(
        default="gemini-2.5-flash", alias="LLM_GUARDRAILS_MODEL"
    )
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")

    # Database
    sqlite_db: str = Field(default="app_dev.db", alias="SQLITE_DB")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
