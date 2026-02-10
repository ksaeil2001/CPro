import math

import structlog

from app.pipeline.base import PipelineContext, PipelineStage
from app.schemas.pipeline import MappedTranslation

logger = structlog.get_logger()

MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 40


class TranslationMapper(PipelineStage):
    """GAP-C: Map translated text back to regions with font size estimation."""

    name = "translation_mapper"

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        raw_translations = ctx.metadata.get("raw_translations", [])

        # Build lookup: region_id → translated text
        translated_map: dict[int, str] = {}
        for t in raw_translations:
            tid = t.get("id")
            text = t.get("text", "")
            if tid is not None and text:
                translated_map[tid] = text

        mapped = []
        for region in ctx.regions:
            translated_text = translated_map.get(region.id)
            if not translated_text:
                continue

            # Use balloon bbox if available, otherwise use region bbox
            bbox = region.balloon_bbox or region.bbox
            bbox_w = bbox[2] - bbox[0]
            bbox_h = bbox[3] - bbox[1]

            # Estimate font size to fit text within bbox
            font_size = self._estimate_font_size(
                translated_text, bbox_w, bbox_h
            )

            mapped.append(
                MappedTranslation(
                    region_id=region.id,
                    bbox=bbox,
                    translated=translated_text,
                    font_size=font_size,
                    balloon_info={"width": bbox_w, "height": bbox_h},
                )
            )

        ctx.translations = mapped

        logger.info(
            "translation_mapper.mapped",
            total_regions=len(ctx.regions),
            mapped_count=len(mapped),
            job_id=str(ctx.job_id),
        )
        return ctx

    def _estimate_font_size(self, text: str, box_w: int, box_h: int) -> int:
        """Estimate the largest font size that fits text within the box.

        Uses a simple area-based heuristic: each character occupies
        roughly font_size^2 pixels.
        """
        char_count = max(len(text.replace("\n", "")), 1)
        # Usable area with padding
        usable_w = box_w * 0.85
        usable_h = box_h * 0.85
        usable_area = usable_w * usable_h

        # Approximate: each char needs font_size * (font_size * 0.6) pixels
        # So total area ≈ char_count * font_size^2 * 0.6
        font_size = int(math.sqrt(usable_area / (char_count * 0.6)))
        font_size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, font_size))

        # Also check that characters per line is reasonable
        chars_per_line = max(1, int(usable_w / (font_size * 0.6)))
        lines_needed = math.ceil(char_count / chars_per_line)
        total_text_height = lines_needed * font_size * 1.3

        # If text overflows vertically, reduce font size
        if total_text_height > usable_h:
            font_size = max(
                MIN_FONT_SIZE,
                int(font_size * usable_h / total_text_height),
            )

        return font_size
