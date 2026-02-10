from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = ""  # Must be set via DATABASE_URL env var
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle_s: int = 3600

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_s: int = 30
    openai_max_retries: int = 2

    # Google Vision (backup OCR)
    google_application_credentials: str = ""

    # Replicate (backup inpainting)
    replicate_api_token: str = ""

    # Cost limits
    max_cost_per_page_krw: float = 10.0
    daily_cost_limit_krw: float = 10000.0
    usd_krw_rate: float = 1400.0

    # App
    log_level: str = "INFO"
    debug: bool = False

    # CORS
    allowed_origins: str = "http://localhost:3000"  # Comma-separated list

    # Upload limits
    max_upload_size_bytes: int = 20 * 1024 * 1024  # 20 MB
    max_image_dimension: int = 10000

    # Fonts
    font_path: str = "/app/fonts/NotoSansKR-Regular.ttf"
    font_download_url: str = (
        "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
    )
    ensure_font_on_startup: bool = True

    # Result storage
    result_dir: str = "/tmp/results"
    result_ttl_hours: int = 24
    cleanup_interval_minutes: int = 60

    # Model preloading
    preload_models: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Validators
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure DATABASE_URL is set and properly formatted."""
        if not v:
            raise ValueError(
                "DATABASE_URL is required.\n"
                "Please set the DATABASE_URL environment variable.\n"
                "Example: postgresql+asyncpg://user:password@host:5432/dbname\n"
                "For development, use docker-compose which sets this automatically."
            )

        # Basic format validation
        if not v.startswith(("postgresql+asyncpg://", "sqlite+aiosqlite://")):
            raise ValueError(
                f"DATABASE_URL must start with 'postgresql+asyncpg://' or 'sqlite+aiosqlite://'\n"
                f"Got: {v[:50]}..."
            )

        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Ensure OPENAI_API_KEY is set and properly formatted."""
        if not v:
            raise ValueError(
                "OPENAI_API_KEY is required for translation functionality.\n"
                "Please set the OPENAI_API_KEY environment variable.\n"
                "Get your API key from: https://platform.openai.com/api-keys\n"
                "Example: OPENAI_API_KEY=sk-proj-..."
            )

        # Validate format (OpenAI keys start with 'sk-')
        if not v.startswith("sk-"):
            raise ValueError(
                f"OPENAI_API_KEY appears invalid.\n"
                f"OpenAI API keys should start with 'sk-'\n"
                f"Got: {v[:10]}... (first 10 characters)"
            )

        # Warn if key looks too short (typical keys are 40+ chars)
        if len(v) < 20:
            raise ValueError(
                f"OPENAI_API_KEY appears too short (got {len(v)} characters).\n"
                f"Valid API keys are typically 40+ characters."
            )

        return v


settings = Settings()
