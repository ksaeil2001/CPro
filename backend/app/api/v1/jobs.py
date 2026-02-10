import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.job import JobStatusResponse, PipelineLogResponse
from app.services.job_service import get_job, get_job_logs

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the status of a translation job."""
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        page_count=job.page_count,
        total_cost_krw=job.total_cost_krw,
        processing_time_ms=job.processing_time_ms,
        error_message=job.error_message,
        warnings=json.loads(job.warnings_json) if job.warnings_json else [],
        current_stage=job.current_stage,
        created_at=job.created_at,
    )


@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: uuid.UUID):
    """Download the translated image result."""
    result_path = os.path.join(settings.result_dir, f"{job_id}.png")
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result not ready or not found")

    return FileResponse(
        result_path,
        media_type="image/png",
        filename=f"translated_{job_id}.png",
    )


@router.get("/jobs/{job_id}/original")
async def get_job_original(job_id: uuid.UUID):
    """Download the original uploaded image."""
    original_path = os.path.join(settings.result_dir, f"{job_id}_original.png")
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Original image not found")

    return FileResponse(
        original_path,
        media_type="image/png",
        filename=f"original_{job_id}.png",
    )


@router.get("/jobs/{job_id}/logs", response_model=list[PipelineLogResponse])
async def get_job_pipeline_logs(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline execution logs for a job."""
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = await get_job_logs(db, job_id)
    return [
        PipelineLogResponse(
            stage=log.stage,
            duration_ms=log.duration_ms,
            cost_krw=log.cost_krw,
            tokens_used=log.tokens_used,
            success=log.success,
            failure_type=log.failure_type,
        )
        for log in logs
    ]
