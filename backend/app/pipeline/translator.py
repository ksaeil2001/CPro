import json

import structlog
from openai import AsyncOpenAI

from app.core.config import settings
from app.pipeline.base import PipelineContext, PipelineStage
from app.services.circuit_breaker import CircuitBreaker

logger = structlog.get_logger()


class Translator(PipelineStage):
    """STAGE ③: Translate text using GPT-4o-mini."""

    name = "translator"

    def __init__(self, circuit_breaker: CircuitBreaker | None = None):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.circuit_breaker = circuit_breaker or CircuitBreaker("openai")

    async def process(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.translation_prompt:
            logger.info("translator.skipped_no_prompt", job_id=str(ctx.job_id))
            ctx.metadata["raw_translations"] = []
            return ctx

        system_prompt = ctx.metadata.get(
            "translation_system_prompt", "Translate Japanese to Korean."
        )

        async def _call_openai():
            return await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ctx.translation_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

        response = await self.circuit_breaker.call(_call_openai)

        # Calculate cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = input_tokens + output_tokens

        # GPT-4o-mini pricing: $0.15/1M input, $0.60/1M output
        cost_usd = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
        cost_krw = cost_usd * settings.usd_krw_rate

        ctx.metadata["translator_cost_krw"] = cost_krw
        ctx.metadata["translator_tokens"] = total_tokens

        # Parse response
        raw_content = response.choices[0].message.content
        try:
            parsed = json.loads(raw_content)
            translations = parsed.get("translations", [])
        except json.JSONDecodeError:
            logger.error(
                "translator.json_parse_error",
                content=raw_content[:200],
                job_id=str(ctx.job_id),
            )
            translations = []

        ctx.metadata["raw_translations"] = translations

        logger.info(
            "translator.completed",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_krw=f"{cost_krw:.4f}",
            translation_count=len(translations),
            job_id=str(ctx.job_id),
        )
        return ctx
