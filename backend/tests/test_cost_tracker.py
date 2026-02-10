import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cost_tracker import BudgetExceededError, CostTracker


class TestCostTracker:
    @pytest.mark.asyncio
    async def test_record_stage_accumulates_cost(self, mock_db_session):
        tracker = CostTracker(uuid.uuid4(), mock_db_session, max_cost_krw=10.0)

        await tracker.record_stage(stage="translator", duration_ms=100, cost_krw=2.0)
        assert tracker.accumulated_krw == 2.0

        await tracker.record_stage(stage="translator2", duration_ms=50, cost_krw=3.0)
        assert tracker.accumulated_krw == 5.0

    @pytest.mark.asyncio
    async def test_budget_exceeded_raises(self, mock_db_session):
        tracker = CostTracker(uuid.uuid4(), mock_db_session, max_cost_krw=5.0)

        await tracker.record_stage(stage="stage1", duration_ms=100, cost_krw=3.0)

        with pytest.raises(BudgetExceededError, match="Budget exceeded"):
            await tracker.record_stage(stage="stage2", duration_ms=100, cost_krw=3.0)

    @pytest.mark.asyncio
    async def test_zero_cost_stages_ok(self, mock_db_session):
        tracker = CostTracker(uuid.uuid4(), mock_db_session, max_cost_krw=1.0)

        for i in range(10):
            await tracker.record_stage(stage=f"stage{i}", duration_ms=50, cost_krw=0.0)

        assert tracker.accumulated_krw == 0.0

    @pytest.mark.asyncio
    async def test_finalize_updates_job(self, mock_db_session):
        job_id = uuid.uuid4()
        mock_job = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_job
        mock_db_session.execute.return_value = mock_result

        tracker = CostTracker(job_id, mock_db_session, max_cost_krw=10.0)
        await tracker.record_stage(stage="translator", duration_ms=200, cost_krw=1.5)

        await tracker.finalize(processing_time_ms=500)

        assert mock_job.total_cost_krw == 1.5
        assert mock_job.processing_time_ms == 500
        mock_db_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_record_stage_persists_log_entry(self, mock_db_session):
        tracker = CostTracker(uuid.uuid4(), mock_db_session, max_cost_krw=10.0)

        await tracker.record_stage(
            stage="detector",
            duration_ms=150,
            cost_krw=0.0,
            success=True,
        )

        # Verify db.add was called with a PipelineLog instance
        mock_db_session.add.assert_called_once()
        log_entry = mock_db_session.add.call_args[0][0]
        assert log_entry.stage == "detector"
        assert log_entry.duration_ms == 150
        assert log_entry.success is True

    @pytest.mark.asyncio
    async def test_failure_stage_recorded(self, mock_db_session):
        tracker = CostTracker(uuid.uuid4(), mock_db_session, max_cost_krw=10.0)

        await tracker.record_stage(
            stage="translator",
            duration_ms=500,
            cost_krw=0.0,
            success=False,
            failure_type="TimeoutError",
            details="Connection timed out",
        )

        log_entry = mock_db_session.add.call_args[0][0]
        assert log_entry.success is False
        assert log_entry.failure_type == "TimeoutError"
        assert log_entry.details == "Connection timed out"
