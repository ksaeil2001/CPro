import os
import uuid

import cv2
import numpy as np
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_factory, get_db
from app.models.job import JobStatus
from app.pipeline.balloon_parser import BalloonParser
from app.pipeline.base import PipelineContext
from app.pipeline.detector import TextDetector
from app.pipeline.inpainter import Inpainter
from app.pipeline.ocr_engine import OcrEngine
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.postprocessor import Postprocessor
from app.pipeline.preprocessor import Preprocessor
from app.pipeline.translation_mapper import TranslationMapper
from app.pipeline.translation_prep import TranslationPrep
from app.pipeline.translator import Translator
from app.pipeline.typesetter import Typesetter
from app.schemas.job import JobCreateResponse
from app.services.circuit_breaker import CircuitBreaker
from app.services.cost_tracker import CostTracker
from app.services.job_service import create_job, update_job_status

logger = structlog.get_logger()

router = APIRouter()

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}

# Shared circuit breaker instances
openai_circuit_breaker = CircuitBreaker("openai", failure_threshold=5, recovery_timeout_s=60)


@router.post("/translate", response_model=JobCreateResponse)
async def translate_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image for translation."""
    # Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
            f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Read file
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    # Create job
    job = await create_job(db, original_filename=file.filename)

    # Store original image for result viewer
    os.makedirs(settings.result_dir, exist_ok=True)
    original_path = os.path.join(settings.result_dir, f"{job.id}_original.png")
    cv2.imwrite(original_path, image)

    # Run pipeline in background
    background_tasks.add_task(run_pipeline, job.id, image)

    return JobCreateResponse(job_id=job.id)


async def run_pipeline(job_id: uuid.UUID, image: np.ndarray) -> None:
    """Execute the full translation pipeline in the background."""
    async with async_session_factory() as db:
        try:
            await update_job_status(db, job_id, JobStatus.PROCESSING)
            await db.commit()

            cost_tracker = CostTracker(
                job_id, db, max_cost_krw=settings.max_cost_per_page_krw
            )

            stages = [
                Preprocessor(),
                TextDetector(),
                BalloonParser(),
                OcrEngine(),
                TranslationPrep(),
                Translator(circuit_breaker=openai_circuit_breaker),
                TranslationMapper(),
                Inpainter(),
                Typesetter(),
                Postprocessor(),
            ]

            orchestrator = PipelineOrchestrator(stages, cost_tracker)
            ctx = PipelineContext(job_id=job_id, original_image=image)
            ctx = await orchestrator.run(ctx)

            # Save result image
            result_bytes = ctx.metadata.get("result_bytes")
            if result_bytes:
                result_path = os.path.join(settings.result_dir, f"{job_id}.png")
                with open(result_path, "wb") as f:
                    f.write(result_bytes)

            await update_job_status(db, job_id, JobStatus.COMPLETED)
            await db.commit()

            logger.info("pipeline.job_completed", job_id=str(job_id))

        except Exception as e:
            logger.error("pipeline.job_failed", job_id=str(job_id), error=str(e))
            await update_job_status(
                db, job_id, JobStatus.FAILED, error_message=str(e)[:500]
            )
            await db.commit()
