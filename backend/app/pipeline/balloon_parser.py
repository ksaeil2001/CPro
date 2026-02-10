import asyncio

import cv2
import numpy as np
import structlog

from app.pipeline.base import PipelineContext, PipelineStage

logger = structlog.get_logger()


class BalloonParser(PipelineStage):
    """GAP-A: Find speech bubble boundaries around detected text regions.

    Refines bounding boxes by finding the enclosing speech bubble contour.
    """

    name = "balloon_parser"

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.preprocessed_image is None or not ctx.regions:
            return ctx

        await asyncio.get_event_loop().run_in_executor(
            None, self._parse_balloons, ctx
        )

        matched = sum(1 for r in ctx.regions if r.balloon_bbox is not None)
        logger.info(
            "balloon_parser.matched",
            total_regions=len(ctx.regions),
            matched_balloons=matched,
            job_id=str(ctx.job_id),
        )
        return ctx

    def _parse_balloons(self, ctx: PipelineContext) -> None:
        gray = cv2.cvtColor(ctx.preprocessed_image, cv2.COLOR_BGR2GRAY)

        # Threshold to find white/light speech bubbles
        _, binary = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)

        # Close small gaps in bubble boundaries
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(
            closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter contours by minimum area
        min_area = 500
        balloon_contours = [
            c for c in contours if cv2.contourArea(c) > min_area
        ]

        for region in ctx.regions:
            rx1, ry1, rx2, ry2 = region.bbox
            center_x = (rx1 + rx2) // 2
            center_y = (ry1 + ry2) // 2

            best_contour = None
            best_area = float("inf")

            for contour in balloon_contours:
                # Check if region center is inside this contour
                if cv2.pointPolygonTest(contour, (center_x, center_y), False) >= 0:
                    area = cv2.contourArea(contour)
                    # Pick the smallest contour that contains the region
                    if area < best_area:
                        best_area = area
                        best_contour = contour

            if best_contour is not None:
                bx, by, bw, bh = cv2.boundingRect(best_contour)
                region.balloon_bbox = (bx, by, bx + bw, by + bh)
