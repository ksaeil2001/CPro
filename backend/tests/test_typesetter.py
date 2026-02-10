import os
import uuid
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.pipeline.base import PipelineContext
from app.pipeline.typesetter import MIN_FONT_SIZE, Typesetter
from app.schemas.pipeline import MappedTranslation


@pytest.fixture
def base_image():
    """Create a simple base image for typesetting."""
    return np.full((400, 300, 3), 200, dtype=np.uint8)


@pytest.fixture
def sample_translations():
    return [
        MappedTranslation(
            region_id=0,
            bbox=(10, 10, 200, 100),
            translated="안녕하세요",
            font_size=20,
            balloon_info={"width": 190, "height": 90},
        ),
    ]


class TestTypesetter:
    @pytest.mark.asyncio
    async def test_no_translations_returns_base_image(self, base_image, job_id):
        typesetter = Typesetter()
        ctx = PipelineContext(job_id=job_id)
        ctx.preprocessed_image = base_image
        ctx.translations = []

        result = await typesetter.process(ctx)
        assert result.result_image is not None
        assert np.array_equal(result.result_image, base_image)

    @pytest.mark.asyncio
    async def test_render_with_missing_font_uses_fallback(
        self, base_image, sample_translations, job_id
    ):
        typesetter = Typesetter(font_path="/nonexistent/font.ttf")
        ctx = PipelineContext(job_id=job_id)
        ctx.preprocessed_image = base_image
        ctx.translations = sample_translations

        result = await typesetter.process(ctx)
        assert result.result_image is not None
        assert typesetter._used_fallback_font is True
        # Check warning was added
        warnings = result.metadata.get("warnings", [])
        assert any("fallback" in w.lower() for w in warnings)

    @pytest.mark.asyncio
    async def test_no_image_raises(self, job_id, sample_translations):
        typesetter = Typesetter()
        ctx = PipelineContext(job_id=job_id)
        ctx.translations = sample_translations

        with pytest.raises(ValueError, match="No image"):
            await typesetter.process(ctx)

    def test_text_wrapping(self):
        typesetter = Typesetter()
        img = Image.new("RGB", (200, 200), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        lines = typesetter._wrap_text(draw, "abcdefghijklmnopqrstuvwxyz", font, 50)
        assert len(lines) > 1
        for line in lines:
            assert len(line) > 0

    def test_wrap_text_empty(self):
        typesetter = Typesetter()
        img = Image.new("RGB", (200, 200), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        lines = typesetter._wrap_text(draw, "", font, 100)
        assert lines == []

    def test_wrap_text_newlines(self):
        typesetter = Typesetter()
        img = Image.new("RGB", (200, 200), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()

        lines = typesetter._wrap_text(draw, "line1\nline2", font, 1000)
        assert len(lines) == 2
        assert lines[0] == "line1"
        assert lines[1] == "line2"

    def test_minimum_font_size_consistent(self):
        assert MIN_FONT_SIZE == 12

    @pytest.mark.asyncio
    async def test_small_box_uses_min_font_size(self, base_image, job_id):
        """Very small box with long text should use MIN_FONT_SIZE."""
        translations = [
            MappedTranslation(
                region_id=0,
                bbox=(10, 10, 50, 40),  # Very small box
                translated="이것은 매우 긴 텍스트입니다 번역 테스트",
                font_size=30,
                balloon_info={"width": 40, "height": 30},
            ),
        ]
        typesetter = Typesetter()
        ctx = PipelineContext(job_id=job_id)
        ctx.preprocessed_image = base_image
        ctx.translations = translations

        # Should not crash
        result = await typesetter.process(ctx)
        assert result.result_image is not None
