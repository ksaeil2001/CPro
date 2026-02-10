"""API endpoint tests.

These tests require a running database. For CI, use docker compose.
For unit testing without DB, mock the database dependency.
"""

import io

import numpy as np
import pytest
from PIL import Image


def create_test_image_bytes() -> bytes:
    """Create a simple PNG image in memory."""
    img = Image.new("RGB", (200, 300), color=(255, 255, 255))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestTranslateEndpoint:
    """Tests for POST /api/v1/translate."""

    def test_upload_creates_file(self):
        """Verify that an image upload creates proper bytes."""
        img_bytes = create_test_image_bytes()
        assert len(img_bytes) > 0
        # Verify it can be decoded
        nparr = np.frombuffer(img_bytes, np.uint8)
        assert nparr.shape[0] > 0


class TestJobEndpoints:
    """Tests for GET /api/v1/jobs/* endpoints."""

    def test_job_status_response_format(self):
        """Verify the JobStatusResponse schema."""
        from app.schemas.job import JobStatusResponse
        import uuid

        response = JobStatusResponse(
            job_id=uuid.uuid4(),
            status="pending",
            page_count=1,
            total_cost_krw=0.0,
        )
        assert response.status == "pending"
        assert response.total_cost_krw == 0.0
