import asyncio
import os

import cv2
import numpy as np
import structlog
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.pipeline.base import PipelineContext, PipelineStage

logger = structlog.get_logger()

# Padding inside the text box
TEXT_PADDING = 5
# Line height multiplier
LINE_HEIGHT_FACTOR = 1.3
# Minimum font size (consistent with translation_mapper)
MIN_FONT_SIZE = 12


class Typesetter(PipelineStage):
    """STAGE 4-insert: Render translated Korean text onto the image."""

    name = "typesetter"

    def __init__(self, font_path: str | None = None):
        self.font_path = font_path or settings.font_path
        self._used_fallback_font = False

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        base_image = ctx.inpainted_image if ctx.inpainted_image is not None else ctx.preprocessed_image
        if base_image is None:
            raise ValueError("No image to typeset onto")

        if not ctx.translations:
            ctx.result_image = base_image
            return ctx

        self._used_fallback_font = False
        ctx.result_image = await asyncio.get_event_loop().run_in_executor(
            None, self._render, base_image, ctx.translations
        )

        if self._used_fallback_font:
            ctx.metadata.setdefault("warnings", []).append(
                "Font file not found; fallback bitmap font used. Korean text may not render correctly."
            )

        logger.info(
            "typesetter.completed",
            rendered_count=len(ctx.translations),
            job_id=str(ctx.job_id),
        )
        return ctx

    def _render(self, img: np.ndarray, translations) -> np.ndarray:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        draw = ImageDraw.Draw(img_pil)

        for t in translations:
            font = self._load_font(t.font_size)
            x1, y1, x2, y2 = t.bbox
            box_w = x2 - x1 - TEXT_PADDING * 2
            box_h = y2 - y1 - TEXT_PADDING * 2

            if box_w <= 0 or box_h <= 0:
                continue

            # Word-wrap text
            lines = self._wrap_text(draw, t.translated, font, box_w)
            if not lines:
                continue

            # Calculate total text height
            line_height = int(t.font_size * LINE_HEIGHT_FACTOR)
            total_text_h = len(lines) * line_height

            # If text overflows, reduce font size and re-wrap
            if total_text_h > box_h:
                reduced_size = max(MIN_FONT_SIZE, int(t.font_size * box_h / total_text_h))
                font = self._load_font(reduced_size)
                lines = self._wrap_text(draw, t.translated, font, box_w)
                line_height = int(reduced_size * LINE_HEIGHT_FACTOR)
                total_text_h = len(lines) * line_height

            # Center vertically
            y_offset = y1 + TEXT_PADDING + max(0, (box_h - total_text_h) // 2)

            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_w = line_bbox[2] - line_bbox[0]
                # Center horizontally
                x_offset = x1 + TEXT_PADDING + max(0, (box_w - line_w) // 2)

                # Draw white outline for readability
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text(
                            (x_offset + dx, y_offset + dy),
                            line,
                            font=font,
                            fill="white",
                        )
                # Draw black text
                draw.text((x_offset, y_offset), line, font=font, fill="black")

                y_offset += line_height

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        try:
            if os.path.exists(self.font_path):
                return ImageFont.truetype(self.font_path, size)
        except Exception as e:
            logger.warning("typesetter.font_load_error", error=str(e), font_path=self.font_path)
        # Fallback to default font
        logger.warning(
            "typesetter.font_fallback",
            font_path=self.font_path,
            detail="Using default bitmap font - Korean glyphs will NOT render correctly",
        )
        self._used_fallback_font = True
        return ImageFont.load_default()

    def _wrap_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        max_width: int,
    ) -> list[str]:
        """Wrap text to fit within max_width.

        Korean text is wrapped at character level since Korean doesn't use spaces
        as consistently as English.
        """
        if not text:
            return []

        lines = []
        for paragraph in text.split("\n"):
            current = ""
            for char in paragraph:
                test = current + char
                try:
                    test_width = draw.textlength(test, font=font)
                except AttributeError:
                    # Fallback for older Pillow versions
                    test_width = draw.textbbox((0, 0), test, font=font)[2]

                if test_width <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = char
            if current:
                lines.append(current)

        return lines
