import cv2
import structlog

from app.pipeline.base import PipelineContext, PipelineStage

logger = structlog.get_logger()


class Postprocessor(PipelineStage):
    """POST: Encode final image and gather pipeline stats."""

    name = "postprocessor"

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.result_image is None:
            raise ValueError("No result image to encode")

        # Encode to PNG
        success, buffer = cv2.imencode(".png", ctx.result_image)
        if not success:
            raise RuntimeError("Failed to encode result image to PNG")

        ctx.metadata["result_bytes"] = buffer.tobytes()
        ctx.metadata["result_format"] = "png"

        # Gather stats
        total_regions = len(ctx.regions)
        ocr_recognized = len([r for r in ctx.ocr_results if r.text.strip()])
        translations_mapped = len(ctx.translations)

        stats = {
            "total_regions_detected": total_regions,
            "ocr_recognized": ocr_recognized,
            "translations_mapped": translations_mapped,
            "translation_coverage": (
                translations_mapped / total_regions if total_regions > 0 else 0.0
            ),
        }
        ctx.metadata["stats"] = stats

        # Check for potential issues
        if total_regions > 0 and translations_mapped < total_regions * 0.5:
            logger.warning(
                "postprocessor.low_coverage",
                coverage=stats["translation_coverage"],
                job_id=str(ctx.job_id),
            )

        logger.info(
            "postprocessor.completed",
            stats=stats,
            result_size_bytes=len(ctx.metadata["result_bytes"]),
            job_id=str(ctx.job_id),
        )
        return ctx
