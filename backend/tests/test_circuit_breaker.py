import time

import pytest

from app.services.circuit_breaker import CircuitBreaker, CircuitOpenError


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_closed_state_passes_calls(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        result = await cb.call(self._success_func)
        assert result == "ok"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_failure_counting(self):
        cb = CircuitBreaker("test", failure_threshold=3)
        with pytest.raises(ValueError):
            await cb.call(self._fail_func)
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_open_after_threshold(self):
        cb = CircuitBreaker("test", failure_threshold=2)
        for _ in range(2):
            with pytest.raises(ValueError):
                await cb.call(self._fail_func)
        assert cb.state == "OPEN"
        assert cb.failure_count == 2

    @pytest.mark.asyncio
    async def test_open_rejects_calls(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_s=60)
        with pytest.raises(ValueError):
            await cb.call(self._fail_func)
        assert cb.state == "OPEN"

        with pytest.raises(CircuitOpenError):
            await cb.call(self._success_func)

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_s=0)
        with pytest.raises(ValueError):
            await cb.call(self._fail_func)
        assert cb.state == "OPEN"

        # Force last_failure_time to be in the past
        cb.last_failure_time = time.time() - 1

        # Next call should transition to HALF_OPEN and succeed
        result = await cb.call(self._success_func)
        assert result == "ok"
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_half_open_to_closed_on_success(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_s=0)
        with pytest.raises(ValueError):
            await cb.call(self._fail_func)
        cb.last_failure_time = time.time() - 1

        result = await cb.call(self._success_func)
        assert result == "ok"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_to_open_on_failure(self):
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout_s=0)
        with pytest.raises(ValueError):
            await cb.call(self._fail_func)
        cb.last_failure_time = time.time() - 1

        with pytest.raises(ValueError):
            await cb.call(self._fail_func)
        assert cb.state == "OPEN"

    def test_reset(self):
        cb = CircuitBreaker("test")
        cb.state = "OPEN"
        cb.failure_count = 10
        cb.last_failure_time = time.time()

        cb.reset()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    @staticmethod
    async def _success_func():
        return "ok"

    @staticmethod
    async def _fail_func():
        raise ValueError("test error")
