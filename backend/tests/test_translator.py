import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.pipeline.base import PipelineContext
from app.services.circuit_breaker import CircuitBreaker


class TestTranslator:
    @pytest.mark.asyncio
    async def test_successful_translation(self, mock_openai_response):
        translations = [
            {"id": 0, "text": "안녕하세요"},
            {"id": 1, "text": "감사합니다"},
        ]
        response = mock_openai_response(
            content=json.dumps({"translations": translations}),
            input_tokens=200,
            output_tokens=100,
        )

        with patch("app.pipeline.translator.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=response)
            mock_client_cls.return_value = mock_client

            from app.pipeline.translator import Translator

            cb = CircuitBreaker("test")
            translator = Translator(circuit_breaker=cb)
            translator.client = mock_client

            ctx = PipelineContext(job_id=uuid.uuid4())
            ctx.translation_prompt = "Translate these text regions."
            ctx.metadata["translation_entry_count"] = 2

            result = await translator.process(ctx)

            assert len(result.metadata["raw_translations"]) == 2
            assert result.metadata["translator_tokens"] == 300
            assert result.metadata["translator_cost_krw"] > 0

    @pytest.mark.asyncio
    async def test_json_parse_error_returns_empty_with_warning(self, mock_openai_response):
        response = mock_openai_response(content="not valid json {{{")

        with patch("app.pipeline.translator.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=response)
            mock_client_cls.return_value = mock_client

            from app.pipeline.translator import Translator

            cb = CircuitBreaker("test")
            translator = Translator(circuit_breaker=cb)
            translator.client = mock_client

            ctx = PipelineContext(job_id=uuid.uuid4())
            ctx.translation_prompt = "Translate."
            ctx.metadata["translation_entry_count"] = 3

            result = await translator.process(ctx)

            assert result.metadata["raw_translations"] == []
            warnings = result.metadata.get("warnings", [])
            assert any("could not be parsed" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_empty_prompt_skips(self):
        with patch("app.pipeline.translator.AsyncOpenAI"):
            from app.pipeline.translator import Translator

            translator = Translator()

            ctx = PipelineContext(job_id=uuid.uuid4())
            ctx.translation_prompt = ""

            result = await translator.process(ctx)
            assert result.metadata["raw_translations"] == []

    @pytest.mark.asyncio
    async def test_cost_calculation(self, mock_openai_response):
        response = mock_openai_response(
            content='{"translations": []}',
            input_tokens=1000,
            output_tokens=500,
        )

        with patch("app.pipeline.translator.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=response)
            mock_client_cls.return_value = mock_client

            from app.pipeline.translator import Translator

            cb = CircuitBreaker("test")
            translator = Translator(circuit_breaker=cb)
            translator.client = mock_client

            ctx = PipelineContext(job_id=uuid.uuid4())
            ctx.translation_prompt = "Translate."

            result = await translator.process(ctx)

            # GPT-4o-mini: $0.15/1M input + $0.60/1M output
            # (1000 * 0.15 + 500 * 0.60) / 1_000_000 = 0.00045 USD
            # 0.00045 * 1400 = 0.63 KRW
            cost = result.metadata["translator_cost_krw"]
            assert abs(cost - 0.63) < 0.01

    @pytest.mark.asyncio
    async def test_partial_translation_warning(self, mock_openai_response):
        translations = [{"id": 0, "text": "안녕"}]  # Only 1 of 3
        response = mock_openai_response(
            content=json.dumps({"translations": translations})
        )

        with patch("app.pipeline.translator.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=response)
            mock_client_cls.return_value = mock_client

            from app.pipeline.translator import Translator

            cb = CircuitBreaker("test")
            translator = Translator(circuit_breaker=cb)
            translator.client = mock_client

            ctx = PipelineContext(job_id=uuid.uuid4())
            ctx.translation_prompt = "Translate."
            ctx.metadata["translation_entry_count"] = 3

            result = await translator.process(ctx)

            warnings = result.metadata.get("warnings", [])
            assert any("Partial translation" in w for w in warnings)

    @pytest.mark.asyncio
    async def test_zero_results_warning(self, mock_openai_response):
        response = mock_openai_response(content='{"translations": []}')

        with patch("app.pipeline.translator.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=response)
            mock_client_cls.return_value = mock_client

            from app.pipeline.translator import Translator

            cb = CircuitBreaker("test")
            translator = Translator(circuit_breaker=cb)
            translator.client = mock_client

            ctx = PipelineContext(job_id=uuid.uuid4())
            ctx.translation_prompt = "Translate."
            ctx.metadata["translation_entry_count"] = 5

            result = await translator.process(ctx)

            warnings = result.metadata.get("warnings", [])
            assert any("returned 0 results" in w for w in warnings)
