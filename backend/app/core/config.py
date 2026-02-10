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


settings = Settings()
