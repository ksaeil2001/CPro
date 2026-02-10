import uuid

import numpy as np
import pytest


@pytest.fixture
def sample_image() -> np.ndarray:
    """Create a simple test image (white background with black rectangle)."""
    img = np.full((600, 400, 3), 255, dtype=np.uint8)
    # Draw a black rectangle simulating text
    img[100:150, 50:350] = 0
    # Draw another text region
    img[200:260, 80:320] = 0
    return img


@pytest.fixture
def sample_manga_image() -> np.ndarray:
    """Create a more realistic manga-like test image.

    White speech bubbles on gray background with black text areas.
    """
    # Gray background
    img = np.full((800, 600, 3), 200, dtype=np.uint8)

    # White speech bubble 1 (top-right for RTL)
    img[50:200, 350:550] = 255
    # Black text inside bubble 1
    img[80:100, 380:520] = 0
    img[110:130, 370:530] = 0

    # White speech bubble 2 (middle-left)
    img[250:400, 50:250] = 255
    # Black text inside bubble 2
    img[280:300, 80:220] = 0
    img[310:330, 70:230] = 0
    img[340:360, 90:210] = 0

    return img


@pytest.fixture
def job_id() -> uuid.UUID:
    return uuid.uuid4()
