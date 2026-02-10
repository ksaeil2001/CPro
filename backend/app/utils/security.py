"""Security utilities for path validation and sanitization."""

import os
from pathlib import Path
from typing import Union
from uuid import UUID

from fastapi import HTTPException


def validate_safe_path(
    base_dir: Union[str, Path],
    filename: str,
    *,
    allow_create: bool = False,
) -> Path:
    """
    Validate that a file path is safe and within the allowed directory.

    Args:
        base_dir: The base directory that files must be within
        filename: The filename or relative path to validate
        allow_create: If True, don't require the file to exist

    Returns:
        Resolved absolute Path object

    Raises:
        HTTPException: If the path is invalid or outside base_dir
    """
    # Convert to Path objects and resolve to absolute paths
    base_path = Path(base_dir).resolve()

    # Join the paths and resolve
    target_path = (base_path / filename).resolve()

    # Ensure the resolved path is within base_dir
    try:
        target_path.relative_to(base_path)
    except ValueError:
        # Path is outside base_dir - potential path traversal attack
        raise HTTPException(
            status_code=400,
            detail="Invalid file path: access denied",
        )

    # Check if file exists (unless allow_create is True)
    if not allow_create and not target_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return target_path


def get_job_result_path(
    result_dir: Union[str, Path],
    job_id: UUID,
    *,
    original: bool = False,
    check_exists: bool = True,
) -> Path:
    """
    Get the safe file path for a job result or original image.

    Args:
        result_dir: The results directory
        job_id: The job UUID
        original: If True, return path to original image
        check_exists: If True, verify the file exists

    Returns:
        Validated Path object

    Raises:
        HTTPException: If path is invalid or file not found
    """
    suffix = "_original" if original else ""
    filename = f"{job_id}{suffix}.png"

    return validate_safe_path(
        result_dir,
        filename,
        allow_create=not check_exists,
    )
