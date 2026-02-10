import uuid
from unittest.mock import AsyncMock, MagicMock

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


@pytest.fixture
def mock_db_session():
    """Create a mocked AsyncSession for unit tests."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI chat completion response."""

    def _make(content: str = '{"translations": []}', input_tokens: int = 100, output_tokens: int = 50):
        response = MagicMock()
        response.usage.prompt_tokens = input_tokens
        response.usage.completion_tokens = output_tokens
        response.choices = [MagicMock()]
        response.choices[0].message.content = content
        return response

    return _make
