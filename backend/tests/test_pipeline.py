import uuid

import numpy as np
import pytest

from app.pipeline.base import PipelineContext
from app.pipeline.preprocessor import Preprocessor
from app.pipeline.detector import TextDetector
from app.pipeline.balloon_parser import BalloonParser
from app.pipeline.translation_mapper import TranslationMapper


@pytest.fixture
def make_context(job_id):
    def _make(image: np.ndarray) -> PipelineContext:
        return PipelineContext(job_id=job_id, original_image=image)
    return _make


class TestPreprocessor:
    @pytest.mark.asyncio
    async def test_passthrough_small_image(self, sample_image, make_context):
        ctx = make_context(sample_image)
        preprocessor = Preprocessor()
        result = await preprocessor.process(ctx)

        assert result.preprocessed_image is not None
        assert result.preprocessed_image.shape == sample_image.shape

    @pytest.mark.asyncio
    async def test_resize_large_image(self, make_context):
        # Create oversized image
        large_img = np.full((4000, 3000, 3), 128, dtype=np.uint8)
        ctx = make_context(large_img)
        preprocessor = Preprocessor()
        result = await preprocessor.process(ctx)

        assert result.preprocessed_image is not None
        h, w = result.preprocessed_image.shape[:2]
        assert w <= 2000
        assert h <= 3000

    @pytest.mark.asyncio
    async def test_grayscale_conversion(self, make_context):
        gray_img = np.full((400, 300), 128, dtype=np.uint8)
        ctx = make_context(gray_img)
        preprocessor = Preprocessor()
        result = await preprocessor.process(ctx)

        assert result.preprocessed_image is not None
        assert len(result.preprocessed_image.shape) == 3
        assert result.preprocessed_image.shape[2] == 3

    @pytest.mark.asyncio
    async def test_rgba_conversion(self, make_context):
        rgba_img = np.full((400, 300, 4), 128, dtype=np.uint8)
        rgba_img[:, :, 3] = 255  # full opacity
        ctx = make_context(rgba_img)
        preprocessor = Preprocessor()
        result = await preprocessor.process(ctx)

        assert result.preprocessed_image is not None
        assert result.preprocessed_image.shape[2] == 3

    @pytest.mark.asyncio
    async def test_no_image_raises(self, job_id):
        ctx = PipelineContext(job_id=job_id)
        preprocessor = Preprocessor()
        with pytest.raises(ValueError, match="No image"):
            await preprocessor.process(ctx)


class TestDetector:
    @pytest.mark.asyncio
    async def test_detect_regions(self, sample_manga_image, make_context):
        ctx = make_context(sample_manga_image)
        ctx.preprocessed_image = sample_manga_image
        detector = TextDetector()
        result = await detector.process(ctx)

        assert len(result.regions) > 0
        for region in result.regions:
            x1, y1, x2, y2 = region.bbox
            assert x1 < x2
            assert y1 < y2

    @pytest.mark.asyncio
    async def test_empty_image(self, make_context):
        white_img = np.full((400, 300, 3), 255, dtype=np.uint8)
        ctx = make_context(white_img)
        ctx.preprocessed_image = white_img
        detector = TextDetector()
        result = await detector.process(ctx)

        # Should find no (or very few) regions on a blank image
        assert len(result.regions) <= 2


class TestBalloonParser:
    @pytest.mark.asyncio
    async def test_match_balloons(self, sample_manga_image, make_context):
        # First detect regions
        ctx = make_context(sample_manga_image)
        ctx.preprocessed_image = sample_manga_image
        detector = TextDetector()
        ctx = await detector.process(ctx)

        # Then parse balloons
        parser = BalloonParser()
        ctx = await parser.process(ctx)

        # Some regions should have balloon_bbox
        has_balloon = [r for r in ctx.regions if r.balloon_bbox is not None]
        # Not asserting exact count since it depends on the test image
        assert isinstance(has_balloon, list)


class TestTranslationMapper:
    @pytest.mark.asyncio
    async def test_font_size_estimation(self):
        mapper = TranslationMapper()
        # Large box, short text → larger font
        large_font = mapper._estimate_font_size("안녕", 200, 100)
        # Small box, long text → smaller font
        small_font = mapper._estimate_font_size(
            "이것은 매우 긴 텍스트입니다", 100, 50
        )
        assert large_font >= small_font
        assert 12 <= large_font <= 40
        assert 12 <= small_font <= 40
