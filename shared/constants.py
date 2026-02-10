# Pipeline stage names
STAGE_PREPROCESSOR = "preprocessor"
STAGE_DETECTOR = "detector"
STAGE_BALLOON_PARSER = "balloon_parser"
STAGE_OCR_ENGINE = "ocr_engine"
STAGE_TRANSLATION_PREP = "translation_prep"
STAGE_TRANSLATOR = "translator"
STAGE_TRANSLATION_MAPPER = "translation_mapper"
STAGE_INPAINTER = "inpainter"
STAGE_TYPESETTER = "typesetter"
STAGE_POSTPROCESSOR = "postprocessor"

PIPELINE_STAGES = [
    STAGE_PREPROCESSOR,
    STAGE_DETECTOR,
    STAGE_BALLOON_PARSER,
    STAGE_OCR_ENGINE,
    STAGE_TRANSLATION_PREP,
    STAGE_TRANSLATOR,
    STAGE_TRANSLATION_MAPPER,
    STAGE_INPAINTER,
    STAGE_TYPESETTER,
    STAGE_POSTPROCESSOR,
]

# Region types
REGION_DIALOGUE = "dialogue"
REGION_NARRATION = "narration"
REGION_SFX = "sfx"

# Job statuses
JOB_PENDING = "pending"
JOB_PROCESSING = "processing"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"

# Font paths
FONT_NOTO_SANS_KR = "/app/fonts/NotoSansKR-Regular.ttf"

# Cost calculation (GPT-4o-mini)
GPT4O_MINI_INPUT_PRICE_PER_1M = 0.15  # USD
GPT4O_MINI_OUTPUT_PRICE_PER_1M = 0.60  # USD
