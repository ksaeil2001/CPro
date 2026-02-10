import asyncio

import cv2
import numpy as np
import structlog

from app.pipeline.base import PipelineContext, PipelineStage
from app.schemas.pipeline import DetectedRegion

logger = structlog.get_logger()

# Minimum area for a text region (filters out noise)
MIN_REGION_AREA = 200
# Minimum aspect ratio height/width to filter horizontal lines
MIN_ASPECT_RATIO = 0.1


class TextDetector(PipelineStage):
    """STAGE ①: Detect text regions in the image.

    Uses OpenCV-based contour detection as the primary method.
    CRAFT can be added as an enhancement in Phase 2.
    """

    name = "detector"

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.preprocessed_image is None:
            raise ValueError("No preprocessed image")

        regions = await asyncio.get_event_loop().run_in_executor(
            None, self._detect, ctx.preprocessed_image
        )

        ctx.regions = regions
        logger.info(
            "detector.found_regions",
            count=len(regions),
            job_id=str(ctx.job_id),
        )
        return ctx

    def _detect(self, img: np.ndarray) -> list[DetectedRegion]:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        # Adaptive threshold to handle varying backgrounds
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10
        )

        # Morphological operations to connect text characters
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15))

        # Detect horizontal and vertical text groups
        dilated_h = cv2.dilate(binary, kernel_h, iterations=2)
        dilated_v = cv2.dilate(binary, kernel_v, iterations=2)
        combined = cv2.bitwise_or(dilated_h, dilated_v)

        # Further dilation to merge nearby text regions
        kernel_merge = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        merged = cv2.dilate(combined, kernel_merge, iterations=1)

        contours, _ = cv2.findContours(
            merged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        regions = []
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cw * ch

            # Filter out too small or too thin regions
            if area < MIN_REGION_AREA:
                continue
            if ch / max(cw, 1) < MIN_ASPECT_RATIO and cw / max(ch, 1) < MIN_ASPECT_RATIO:
                continue
            # Filter out regions that span the entire image (likely borders)
            if cw > w * 0.9 and ch > h * 0.9:
                continue

            regions.append(
                DetectedRegion(
                    id=len(regions),
                    bbox=(x, y, x + cw, y + ch),
                    region_type="dialogue",
                    confidence=0.8,
                    reading_order=0,
                )
            )

        # Sort by reading order: right-to-left, top-to-bottom (RTL manga)
        regions.sort(key=lambda r: (-r.bbox[0], r.bbox[1]))
        for idx, region in enumerate(regions):
            region.reading_order = idx
            region.id = idx

        return regions
