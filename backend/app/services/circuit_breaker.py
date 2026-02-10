import time
from collections.abc import Callable
from typing import Any

import structlog

logger = structlog.get_logger()


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    """Simple circuit breaker for external API calls.

    States:
      CLOSED  — normal operation, failures are counted
      OPEN    — calls are rejected immediately
      HALF_OPEN — one test call is allowed through
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_s: int = 60,
    ):
        self.name = name
        self.state = "CLOSED"
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.last_failure_time: float | None = None

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        if self.state == "OPEN":
            if (
                self.last_failure_time is not None
                and time.time() - self.last_failure_time > self.recovery_timeout_s
            ):
                logger.info("circuit_breaker.half_open", name=self.name)
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is OPEN — call rejected"
                )

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                logger.info("circuit_breaker.recovered", name=self.name)
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    "circuit_breaker.opened",
                    name=self.name,
                    failure_count=self.failure_count,
                )
                self.state = "OPEN"
            raise e

    def reset(self) -> None:
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
