import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.pipeline_log import PipelineLog

logger = structlog.get_logger()


class BudgetExceededError(Exception):
    pass


class CostTracker:
    """Tracks per-stage costs and enforces budget limits."""

    def __init__(
        self, job_id: uuid.UUID, db: AsyncSession, max_cost_krw: float = 10.0
    ):
        self.job_id = job_id
        self.db = db
        self.max_cost_krw = max_cost_krw
        self.accumulated_krw = 0.0

    async def record_stage(
        self,
        stage: str,
        duration_ms: int,
        cost_krw: float = 0.0,
        tokens: int | None = None,
        success: bool = True,
        failure_type: str | None = None,
        details: str | None = None,
    ) -> None:
        log_entry = PipelineLog(
            job_id=self.job_id,
            stage=stage,
            duration_ms=duration_ms,
            cost_krw=cost_krw,
            tokens_used=tokens,
            success=success,
            failure_type=failure_type,
            details=details,
        )
        self.db.add(log_entry)
        await self.db.flush()

        self.accumulated_krw += cost_krw

        logger.info(
            "cost_tracker.stage_recorded",
            job_id=str(self.job_id),
            stage=stage,
            cost_krw=cost_krw,
            accumulated_krw=self.accumulated_krw,
            success=success,
        )

        if self.accumulated_krw > self.max_cost_krw:
            logger.warning(
                "cost_tracker.budget_exceeded",
                job_id=str(self.job_id),
                accumulated_krw=self.accumulated_krw,
                limit_krw=self.max_cost_krw,
            )
            raise BudgetExceededError(
                f"Budget exceeded: {self.accumulated_krw:.2f} KRW > {self.max_cost_krw:.2f} KRW"
            )

    async def finalize(self, processing_time_ms: int) -> None:
        result = await self.db.execute(select(Job).where(Job.id == self.job_id))
        job = result.scalar_one()
        job.total_cost_krw = self.accumulated_krw
        job.processing_time_ms = processing_time_ms
        await self.db.flush()

        logger.info(
            "cost_tracker.finalized",
            job_id=str(self.job_id),
            total_cost_krw=self.accumulated_krw,
            processing_time_ms=processing_time_ms,
        )
