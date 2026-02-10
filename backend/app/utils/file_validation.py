"""File validation utilities for secure upload handling."""

from typing import Optional

import cv2
import magic
import numpy as np
import structlog
from fastapi import HTTPException

logger = structlog.get_logger()

# Allowed MIME types based on actual file content
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}


def validate_file_type(file_bytes: bytes, claimed_content_type: Optional[str] = None) -> str:
    """
    Validate file type using magic numbers, not client-provided headers.

    Args:
        file_bytes: The actual file content bytes
        claimed_content_type: Client-provided Content-Type (for logging only)

    Returns:
        The actual MIME type detected from file content

    Raises:
        HTTPException: If file type is not allowed or detection fails
    """
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    # Detect actual MIME type from file content
    try:
        mime = magic.from_buffer(file_bytes, mime=True)
    except Exception as e:
        logger.error("file_validation.magic_detection_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Could not determine file type")

    # Log mismatch between claimed and actual type (potential spoofing attempt)
    if claimed_content_type and claimed_content_type != mime:
        logger.warning(
            "file_validation.content_type_mismatch",
            claimed=claimed_content_type,
            actual=mime,
            spoofing_attempt=True,
        )

    # Validate against allowed types
    if mime not in ALLOWED_MIME_TYPES:
        logger.warning(
            "file_validation.rejected_mime_type",
            mime_type=mime,
            allowed=list(ALLOWED_MIME_TYPES),
        )
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {mime}. "
            f"Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    return mime


def validate_image_decodable(file_bytes: bytes) -> np.ndarray:
    """
    Validate that the file can be decoded as an image by OpenCV.

    This provides defense-in-depth: even if magic number validation passes,
    we ensure the file is actually a valid, decodable image.

    Args:
        file_bytes: The file content bytes

    Returns:
        Decoded image as numpy array

    Raises:
        HTTPException: If image cannot be decoded
    """
    try:
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

        if image is None:
            raise HTTPException(
                status_code=400,
                detail="File appears to be an image but could not be decoded. "
                "The file may be corrupted or use an unsupported variant.",
            )

        return image

    except HTTPException:
        raise
    except Exception as e:
        logger.error("file_validation.decode_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Could not decode image file")


def validate_upload(
    file_bytes: bytes,
    claimed_content_type: Optional[str] = None,
    max_dimension: int = 10000,
) -> tuple[np.ndarray, str]:
    """
    Complete upload validation pipeline.

    Performs comprehensive validation:
    1. Magic number validation (actual file content)
    2. Image decode validation (ensure it's truly an image)
    3. Dimension validation (security limits)

    Args:
        file_bytes: The uploaded file content
        claimed_content_type: Client-provided Content-Type header
        max_dimension: Maximum allowed image dimension

    Returns:
        Tuple of (decoded image array, actual MIME type)

    Raises:
        HTTPException: If any validation fails
    """
    # Step 1: Validate actual file type (not trusting client)
    actual_mime = validate_file_type(file_bytes, claimed_content_type)

    # Step 2: Validate it's actually a decodable image
    image = validate_image_decodable(file_bytes)

    # Step 3: Validate dimensions
    h, w = image.shape[:2]
    if h > max_dimension or w > max_dimension:
        raise HTTPException(
            status_code=400,
            detail=f"Image dimensions {w}x{h} exceed maximum {max_dimension}x{max_dimension}",
        )

    logger.info(
        "file_validation.success",
        mime_type=actual_mime,
        dimensions=f"{w}x{h}",
        size_bytes=len(file_bytes),
    )

    return image, actual_mime
