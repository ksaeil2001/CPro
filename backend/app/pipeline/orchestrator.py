import time

import structlog

from app.pipeline.base import PipelineContext, PipelineStage
from app.services.cost_tracker import CostTracker

logger = structlog.get_logger()


class PipelineOrchestrator:
    """Runs pipeline stages sequentially with timing, cost tracking, and error handling."""

    def __init__(self, stages: list[PipelineStage], cost_tracker: CostTracker):
        self.stages = stages
        self.cost_tracker = cost_tracker

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        total_start = time.monotonic()

        for stage in self.stages:
            stage_start = time.monotonic()
            logger.info(
                "pipeline.stage.start",
                stage=stage.name,
                job_id=str(ctx.job_id),
            )

            try:
                ctx = await stage.process(ctx)
                duration_ms = int((time.monotonic() - stage_start) * 1000)
                cost = ctx.metadata.get(f"{stage.name}_cost_krw", 0.0)
                tokens = ctx.metadata.get(f"{stage.name}_tokens", None)

                await self.cost_tracker.record_stage(
                    stage=stage.name,
                    duration_ms=duration_ms,
                    cost_krw=cost,
                    tokens=tokens,
                )
                logger.info(
                    "pipeline.stage.complete",
                    stage=stage.name,
                    duration_ms=duration_ms,
                    cost_krw=cost,
                    job_id=str(ctx.job_id),
                )

            except Exception as e:
                duration_ms = int((time.monotonic() - stage_start) * 1000)
                await self.cost_tracker.record_stage(
                    stage=stage.name,
                    duration_ms=duration_ms,
                    cost_krw=0,
                    success=False,
                    failure_type=type(e).__name__,
                    details=str(e)[:500],
                )
                logger.error(
                    "pipeline.stage.failed",
                    stage=stage.name,
                    error=str(e),
                    job_id=str(ctx.job_id),
                )
                raise

        total_ms = int((time.monotonic() - total_start) * 1000)
        await self.cost_tracker.finalize(total_ms)

        logger.info(
            "pipeline.complete",
            job_id=str(ctx.job_id),
            total_ms=total_ms,
            total_cost_krw=self.cost_tracker.accumulated_krw,
        )
        return ctx
