import asyncio

import cv2
import numpy as np
import structlog

from app.pipeline.base import PipelineContext, PipelineStage

logger = structlog.get_logger()

MAX_WIDTH = 2000
MAX_HEIGHT = 3000


class Preprocessor(PipelineStage):
    """PRE: Normalize input image — resize, convert color space."""

    name = "preprocessor"

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        img = ctx.original_image
        if img is None:
            raise ValueError("No image provided in context")

        img = await asyncio.get_event_loop().run_in_executor(
            None, self._normalize, img
        )
        ctx.preprocessed_image = img
        return ctx

    def _normalize(self, img: np.ndarray) -> np.ndarray:
        # Handle RGBA → RGB (composite on white background)
        if len(img.shape) == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3:4] / 255.0
            rgb = img[:, :, :3]
            white_bg = np.full_like(rgb, 255)
            img = (rgb * alpha + white_bg * (1 - alpha)).astype(np.uint8)

        # Handle grayscale → BGR
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        h, w = img.shape[:2]

        # Resize if too large (preserve aspect ratio)
        if w > MAX_WIDTH or h > MAX_HEIGHT:
            scale = min(MAX_WIDTH / w, MAX_HEIGHT / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(
                "preprocessor.resized",
                original=f"{w}x{h}",
                resized=f"{new_w}x{new_h}",
            )

        return img
