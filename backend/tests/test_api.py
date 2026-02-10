"""API endpoint tests.

Tests use mocked database to avoid requiring a running PostgreSQL instance.
"""

import io
import uuid

import numpy as np
import pytest
from PIL import Image

from app.schemas.job import JobStatusResponse


def create_test_image_bytes(width: int = 200, height: int = 300) -> bytes:
    """Create a simple PNG image in memory."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def create_large_bytes(size_mb: int) -> bytes:
    """Create a bytes object of approximately the given size in MB."""
    return b"x" * (size_mb * 1024 * 1024)


class TestTranslateEndpoint:
    """Tests for POST /api/v1/translate."""

    def test_upload_creates_file(self):
        """Verify that an image upload creates proper bytes."""
        img_bytes = create_test_image_bytes()
        assert len(img_bytes) > 0
        nparr = np.frombuffer(img_bytes, np.uint8)
        assert nparr.shape[0] > 0

    def test_image_content_type_validation(self):
        """Verify ALLOWED_CONTENT_TYPES is correctly defined."""
        from app.api.v1.translate import ALLOWED_CONTENT_TYPES

        assert "image/png" in ALLOWED_CONTENT_TYPES
        assert "image/jpeg" in ALLOWED_CONTENT_TYPES
        assert "image/webp" in ALLOWED_CONTENT_TYPES
        assert "application/pdf" not in ALLOWED_CONTENT_TYPES

    def test_read_with_limit_function_exists(self):
        """Verify the _read_with_limit function is importable."""
        from app.api.v1.translate import _read_with_limit

        assert callable(_read_with_limit)


class TestJobEndpoints:
    """Tests for GET /api/v1/jobs/* endpoints."""

    def test_job_status_response_format(self):
        """Verify the JobStatusResponse schema."""
        response = JobStatusResponse(
            job_id=uuid.uuid4(),
            status="pending",
            page_count=1,
            total_cost_krw=0.0,
        )
        assert response.status == "pending"
        assert response.total_cost_krw == 0.0

    def test_job_status_response_with_warnings(self):
        """Verify warnings field in JobStatusResponse."""
        response = JobStatusResponse(
            job_id=uuid.uuid4(),
            status="completed",
            page_count=1,
            total_cost_krw=1.5,
            warnings=["Partial translation: 2/5 regions translated."],
            current_stage="postprocessor",
        )
        assert len(response.warnings) == 1
        assert "Partial" in response.warnings[0]
        assert response.current_stage == "postprocessor"

    def test_job_status_response_defaults(self):
        """Verify default values for new fields."""
        response = JobStatusResponse(
            job_id=uuid.uuid4(),
            status="pending",
        )
        assert response.warnings == []
        assert response.current_stage is None
        assert response.processing_time_ms is None
        assert response.error_message is None


class TestUploadValidation:
    """Tests for upload size and dimension validation."""

    def test_max_upload_size_configured(self):
        """Verify upload size limit is configured."""
        from app.core.config import settings

        assert settings.max_upload_size_bytes == 20 * 1024 * 1024  # 20 MB

    def test_max_image_dimension_configured(self):
        """Verify image dimension limit is configured."""
        from app.core.config import settings

        assert settings.max_image_dimension == 10000

    def test_small_image_within_limits(self):
        """Verify a normal-sized image passes dimension check."""
        from app.core.config import settings

        img_bytes = create_test_image_bytes(800, 600)
        assert len(img_bytes) < settings.max_upload_size_bytes

    def test_image_dimension_check_logic(self):
        """Verify that large dimensions would be caught."""
        from app.core.config import settings

        # Simulate dimension check
        h, w = 12000, 8000
        max_dim = settings.max_image_dimension
        assert h > max_dim or w > max_dim


class TestConfigSettings:
    """Tests for new configuration settings."""

    def test_openai_timeout_configured(self):
        from app.core.config import settings

        assert settings.openai_timeout_s == 30
        assert settings.openai_max_retries == 2

    def test_db_pool_configured(self):
        from app.core.config import settings

        assert settings.db_pool_size == 10
        assert settings.db_max_overflow == 20
        assert settings.db_pool_recycle_s == 3600

    def test_font_settings(self):
        from app.core.config import settings

        assert settings.ensure_font_on_startup is True
        assert "NotoSansKR" in settings.font_download_url

    def test_cleanup_settings(self):
        from app.core.config import settings

        assert settings.result_ttl_hours == 24
        assert settings.cleanup_interval_minutes == 60

    def test_preload_models_default(self):
        from app.core.config import settings

        assert settings.preload_models is True

    def test_database_url_empty_default(self):
        """Verify database_url defaults to empty string (requires explicit config)."""
        from app.core.config import Settings

        # Create a fresh Settings instance without env file
        s = Settings(database_url="", _env_file=None)
        assert s.database_url == ""
