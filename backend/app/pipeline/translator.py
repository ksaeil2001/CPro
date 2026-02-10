import asyncio
import json

import structlog
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from app.core.config import settings
from app.pipeline.base import PipelineContext, PipelineStage
from app.services.circuit_breaker import CircuitBreaker

logger = structlog.get_logger()


class Translator(PipelineStage):
    """STAGE 3: Translate text using GPT-4o-mini."""

    name = "translator"

    def __init__(self, circuit_breaker: CircuitBreaker | None = None):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_s,
            max_retries=0,  # We handle retries ourselves
        )
        self.circuit_breaker = circuit_breaker or CircuitBreaker("openai")
        self.max_retries = settings.openai_max_retries

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

        # Retry with exponential backoff
        response = await self._call_with_retry(_call_openai, ctx)

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
        expected_count = ctx.metadata.get("translation_entry_count", 0)

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
            ctx.metadata.setdefault("warnings", []).append(
                "Translation response could not be parsed. Text regions will appear blank."
            )

        # Warn about missing translations
        if expected_count > 0 and len(translations) == 0:
            ctx.metadata.setdefault("warnings", []).append(
                f"Translation returned 0 results for {expected_count} text regions."
            )
        elif expected_count > 0 and len(translations) < expected_count:
            ctx.metadata.setdefault("warnings", []).append(
                f"Partial translation: {len(translations)}/{expected_count} regions translated."
            )

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

    async def _call_with_retry(self, func, ctx: PipelineContext):
        """Call OpenAI with retry and exponential backoff."""
        last_error = None
        for attempt in range(1, self.max_retries + 2):
            try:
                return await asyncio.wait_for(
                    self.circuit_breaker.call(func),
                    timeout=settings.openai_timeout_s + 5,
                )
            except (asyncio.TimeoutError, APITimeoutError, APIConnectionError) as e:
                last_error = e
                if attempt <= self.max_retries:
                    wait = 2 ** (attempt - 1)  # 1s, 2s
                    logger.warning(
                        "translator.retry",
                        attempt=attempt,
                        max_retries=self.max_retries,
                        wait_s=wait,
                        error=str(e),
                        job_id=str(ctx.job_id),
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
            except RateLimitError as e:
                last_error = e
                if attempt <= self.max_retries:
                    wait = 4 ** attempt  # 4s, 16s
                    logger.warning(
                        "translator.rate_limited",
                        wait_s=wait,
                        job_id=str(ctx.job_id),
                    )
                    await asyncio.sleep(wait)
                else:
                    raise
        raise last_error
