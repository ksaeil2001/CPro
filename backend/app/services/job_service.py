import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.models.pipeline_log import PipelineLog


async def create_job(
    db: AsyncSession,
    page_count: int = 1,
    original_filename: str | None = None,
) -> Job:
    job = Job(
        status=JobStatus.PENDING,
        page_count=page_count,
        original_filename=original_filename,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def update_job_status(
    db: AsyncSession,
    job_id: uuid.UUID,
    status: JobStatus,
    error_message: str | None = None,
) -> None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one()
    job.status = status
    if error_message:
        job.error_message = error_message
    await db.flush()


async def get_job_logs(
    db: AsyncSession, job_id: uuid.UUID
) -> list[PipelineLog]:
    result = await db.execute(
        select(PipelineLog)
        .where(PipelineLog.job_id == job_id)
        .order_by(PipelineLog.created_at)
    )
    return list(result.scalars().all())
