from pydantic import BaseModel


class TranslationEntry(BaseModel):
    """A single text entry to be translated."""

    id: int
    text: str
    region_type: str = "dialogue"


class TranslationBatch(BaseModel):
    """Batch of text entries for a single translation API call."""

    entries: list[TranslationEntry]
    page_context: str = ""
    source_language: str = "ja"
    target_language: str = "ko"


class TranslatedEntry(BaseModel):
    """A single translated text entry."""

    id: int
    text: str


class TranslationResponse(BaseModel):
    """Response from the translation API."""

    translations: list[TranslatedEntry]
    total_tokens: int = 0
    cost_krw: float = 0.0
