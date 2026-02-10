import asyncio

import cv2
import numpy as np
import structlog
from PIL import Image

from app.pipeline.base import PipelineContext, PipelineStage

logger = structlog.get_logger()

MASK_PADDING = 5


class Inpainter(PipelineStage):
    """STAGE ④-remove: Remove original text using LaMa inpainting."""

    name = "inpainter"

    def __init__(self):
        self._lama = None

    def _get_lama(self):
        """Lazy-load LaMa model."""
        if self._lama is None:
            from simple_lama_inpainting import SimpleLama

            self._lama = SimpleLama()
        return self._lama

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.preprocessed_image is None or not ctx.regions:
            ctx.inpainted_image = ctx.preprocessed_image
            return ctx

        ctx.inpainted_image = await asyncio.get_event_loop().run_in_executor(
            None, self._inpaint, ctx.preprocessed_image, ctx.regions
        )

        logger.info(
            "inpainter.completed",
            regions_inpainted=len(ctx.regions),
            job_id=str(ctx.job_id),
        )
        return ctx

    def _inpaint(self, img: np.ndarray, regions) -> np.ndarray:
        h, w = img.shape[:2]

        # Create mask: white (255) where text should be removed
        mask = np.zeros((h, w), dtype=np.uint8)
        for region in regions:
            x1, y1, x2, y2 = region.bbox
            # Add padding around text region for cleaner inpainting
            x1 = max(0, x1 - MASK_PADDING)
            y1 = max(0, y1 - MASK_PADDING)
            x2 = min(w, x2 + MASK_PADDING)
            y2 = min(h, y2 + MASK_PADDING)
            mask[y1:y2, x1:x2] = 255

        # Convert to PIL for simple-lama
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        mask_pil = Image.fromarray(mask)

        try:
            lama = self._get_lama()
            result_pil = lama(img_pil, mask_pil)
            result = cv2.cvtColor(np.array(result_pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.warning(
                "inpainter.lama_failed_using_simple_fill",
                error=str(e),
            )
            # Fallback: simple white fill
            result = img.copy()
            result[mask == 255] = 255

        return result
