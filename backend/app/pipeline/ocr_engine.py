import asyncio

import numpy as np
import structlog

from app.pipeline.base import PipelineContext, PipelineStage
from app.schemas.pipeline import OcrResult

logger = structlog.get_logger()

# Minimum confidence to accept OCR result
MIN_CONFIDENCE = 0.3


class OcrEngine(PipelineStage):
    """STAGE ②: OCR using PaddleOCR.

    Crops each detected region and runs OCR to extract text.
    """

    name = "ocr_engine"

    def __init__(self):
        self._ocr = None

    def _get_ocr(self):
        """Lazy-load PaddleOCR to avoid import-time overhead."""
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="japan",
                use_gpu=False,
                show_log=False,
            )
        return self._ocr

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.preprocessed_image is None or not ctx.regions:
            return ctx

        results = await asyncio.get_event_loop().run_in_executor(
            None, self._run_ocr, ctx.preprocessed_image, ctx.regions
        )

        ctx.ocr_results = results
        logger.info(
            "ocr_engine.completed",
            total_regions=len(ctx.regions),
            recognized=len([r for r in results if r.text.strip()]),
            job_id=str(ctx.job_id),
        )
        return ctx

    def _run_ocr(self, img: np.ndarray, regions) -> list[OcrResult]:
        ocr = self._get_ocr()
        results = []

        for region in regions:
            x1, y1, x2, y2 = region.bbox
            # Ensure valid crop coordinates
            h, w = img.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 - x1 < 5 or y2 - y1 < 5:
                results.append(
                    OcrResult(region_id=region.id, text="", confidence=0.0)
                )
                continue

            cropped = img[y1:y2, x1:x2]

            try:
                ocr_output = ocr.ocr(cropped, cls=True)
            except Exception as e:
                logger.warning(
                    "ocr_engine.ocr_failed",
                    region_id=region.id,
                    error=str(e),
                )
                results.append(
                    OcrResult(region_id=region.id, text="", confidence=0.0)
                )
                continue

            text_lines = []
            total_confidence = 0.0
            line_count = 0

            if ocr_output and ocr_output[0]:
                for line in ocr_output[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        conf = line[1][1]
                        if conf >= MIN_CONFIDENCE:
                            text_lines.append(text)
                            total_confidence += conf
                            line_count += 1

            full_text = "\n".join(text_lines)
            avg_confidence = total_confidence / line_count if line_count > 0 else 0.0

            results.append(
                OcrResult(
                    region_id=region.id,
                    text=full_text,
                    confidence=avg_confidence,
                    language="ja",
                )
            )

        return results
