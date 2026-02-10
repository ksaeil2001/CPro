import asyncio
import os
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.middleware.rate_limit import limiter
from app.middleware.security_headers import SecurityHeadersMiddleware

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        structlog.get_level_from_name(settings.log_level)
    ),
)
logger = structlog.get_logger()


async def _ensure_font() -> None:
    """Check font file exists; attempt download if missing."""
    font_path = settings.font_path
    if os.path.exists(font_path):
        logger.info("font.found", path=font_path)
        return

    logger.warning("font.missing", path=font_path)
    if not settings.ensure_font_on_startup:
        logger.error("font.download_disabled_but_missing", path=font_path)
        return

    import httpx

    os.makedirs(os.path.dirname(font_path) or ".", exist_ok=True)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(settings.font_download_url)
            resp.raise_for_status()
            with open(font_path, "wb") as f:
                f.write(resp.content)
        logger.info("font.downloaded", path=font_path, size=os.path.getsize(font_path))
    except Exception as e:
        logger.error("font.download_failed", error=str(e), path=font_path)


def _preload_ocr() -> None:
    try:
        from app.pipeline.ocr_engine import get_shared_ocr

        logger.info("startup.preloading_ocr")
        get_shared_ocr()
        logger.info("startup.ocr_ready")
    except Exception as e:
        logger.error("startup.ocr_preload_failed", error=str(e))


def _preload_lama() -> None:
    try:
        from app.pipeline.inpainter import get_shared_lama

        logger.info("startup.preloading_lama")
        get_shared_lama()
        logger.info("startup.lama_ready")
    except Exception as e:
        logger.error("startup.lama_preload_failed", error=str(e))


async def _cleanup_old_results() -> None:
    """Remove files in result_dir older than result_ttl_hours."""
    result_dir = settings.result_dir
    if not os.path.isdir(result_dir):
        return

    cutoff = time.time() - (settings.result_ttl_hours * 3600)
    removed = 0
    for filename in os.listdir(result_dir):
        filepath = os.path.join(result_dir, filename)
        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
            try:
                os.remove(filepath)
                removed += 1
            except OSError as e:
                logger.warning("cleanup.remove_failed", file=filepath, error=str(e))

    if removed > 0:
        logger.info("cleanup.completed", removed_count=removed)


async def _cleanup_loop() -> None:
    """Periodically remove result files older than TTL."""
    while True:
        try:
            await asyncio.sleep(settings.cleanup_interval_minutes * 60)
            await _cleanup_old_results()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("cleanup.error", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_manga_translator_backend")

    # Validate required settings
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Set the DATABASE_URL environment variable or add it to .env"
        )
    if not settings.openai_api_key:
        logger.warning(
            "startup.no_openai_key",
            detail="Translation will fail without an API key",
        )

    # Ensure font file exists
    await _ensure_font()

    # Preload ML models in parallel
    if settings.preload_models:
        logger.info("startup.preloading_models")
        loop = asyncio.get_event_loop()
        ocr_future = loop.run_in_executor(None, _preload_ocr)
        lama_future = loop.run_in_executor(None, _preload_lama)
        await asyncio.gather(ocr_future, lama_future, return_exceptions=True)
        logger.info("startup.models_preloaded")

    # Start result cleanup background task
    cleanup_task = asyncio.create_task(_cleanup_loop())

    yield

    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    await engine.dispose()
    logger.info("shutting_down_manga_translator_backend")


app = FastAPI(
    title="Manga Translator API",
    version="0.1.0",
    description="만화/웹툰 이미지 기반 자동 번역 서비스",
    lifespan=lifespan,
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS with explicit allowed origins from settings
origins_list = [origin.strip() for origin in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Explicit methods only
    allow_headers=["Content-Type", "Authorization"],  # Explicit headers only
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
@limiter.exempt  # Exempt health check from rate limiting
async def health():
    return {"status": "ok"}
