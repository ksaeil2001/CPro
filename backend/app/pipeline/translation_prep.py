import json

import structlog

from app.pipeline.base import PipelineContext, PipelineStage

logger = structlog.get_logger()

SYSTEM_PROMPT = """You are a professional Japanese-to-Korean manga translator.

Rules:
1. Translate naturally into Korean, matching the tone of manga dialogue.
2. For sound effects (SFX/onomatopoeia), provide the Korean equivalent.
3. Preserve the speaker's tone (formal/informal, male/female).
4. Keep translations concise — they must fit in speech bubbles.
5. Do NOT add explanations or notes.
6. Output ONLY valid JSON."""

USER_PROMPT_TEMPLATE = """Translate each text entry from Japanese to Korean.

Input:
{entries_json}

Output ONLY a JSON object with a "translations" key containing an array.
Each entry must have "id" (matching the input) and "text" (Korean translation):
{{"translations": [{{"id": 0, "text": "한국어 번역"}}]}}"""


class TranslationPrep(PipelineStage):
    """GAP-B: Build structured translation prompt from OCR results."""

    name = "translation_prep"

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        entries = []
        for ocr in ctx.ocr_results:
            text = ocr.text.strip()
            if text:
                entries.append({"id": ocr.region_id, "text": text})

        if not entries:
            logger.warning(
                "translation_prep.no_text",
                job_id=str(ctx.job_id),
            )
            ctx.translation_prompt = ""
            return ctx

        entries_json = json.dumps(entries, ensure_ascii=False, indent=2)
        user_prompt = USER_PROMPT_TEMPLATE.format(entries_json=entries_json)

        ctx.translation_prompt = user_prompt
        ctx.metadata["translation_system_prompt"] = SYSTEM_PROMPT
        ctx.metadata["translation_entry_count"] = len(entries)

        logger.info(
            "translation_prep.built_prompt",
            entry_count=len(entries),
            job_id=str(ctx.job_id),
        )
        return ctx
