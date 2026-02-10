from pydantic import BaseModel


class DetectedRegion(BaseModel):
    """A detected text region in the image."""

    id: int
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    region_type: str = "dialogue"  # dialogue | narration | sfx
    confidence: float = 0.0
    reading_order: int = 0
    balloon_bbox: tuple[int, int, int, int] | None = None


class OcrResult(BaseModel):
    """OCR result for a single detected region."""

    region_id: int
    text: str
    confidence: float = 0.0
    language: str = "ja"


class MappedTranslation(BaseModel):
    """A translated text mapped back to its region with rendering info."""

    region_id: int
    bbox: tuple[int, int, int, int]  # render target bbox
    translated: str
    font_size: int
    balloon_info: dict = {}
