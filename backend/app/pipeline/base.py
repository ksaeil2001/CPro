from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

import numpy as np

from app.schemas.pipeline import DetectedRegion, MappedTranslation, OcrResult


@dataclass
class PipelineContext:
    """Mutable context object passed through all pipeline stages.

    Each stage reads what it needs and writes its outputs.
    The orchestrator passes this through stages sequentially.
    """

    job_id: UUID

    # Image data (BGR numpy arrays)
    original_image: np.ndarray | None = None
    preprocessed_image: np.ndarray | None = None
    inpainted_image: np.ndarray | None = None
    result_image: np.ndarray | None = None

    # Pipeline intermediate data
    regions: list[DetectedRegion] = field(default_factory=list)
    ocr_results: list[OcrResult] = field(default_factory=list)
    translations: list[MappedTranslation] = field(default_factory=list)

    # Translation prompt (built by translation_prep, consumed by translator)
    translation_prompt: str = ""

    # Metadata bag for per-stage costs, timings, and intermediate results
    metadata: dict = field(default_factory=dict)


class PipelineStage(ABC):
    """Abstract base class for all pipeline stages."""

    name: str = "unnamed"

    @abstractmethod
    async def process(self, ctx: PipelineContext) -> PipelineContext:
        """Process context and return updated context."""
        ...
