import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.job import JobStatus


class JobCreateResponse(BaseModel):
    job_id: uuid.UUID


class JobStatusResponse(BaseModel):
    job_id: uuid.UUID
    status: JobStatus
    page_count: int = 1
    total_cost_krw: float = 0.0
    processing_time_ms: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PipelineLogResponse(BaseModel):
    stage: str
    duration_ms: int
    cost_krw: float
    tokens_used: int | None = None
    success: bool
    failure_type: str | None = None

    model_config = {"from_attributes": True}
