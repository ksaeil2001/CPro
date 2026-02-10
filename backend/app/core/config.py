from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql+asyncpg://manga:manga_dev_pass@db:5432/manga_translator"
    )

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

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

    # Fonts
    font_path: str = "/app/fonts/NotoSansKR-Regular.ttf"

    # Result storage
    result_dir: str = "/tmp/results"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
