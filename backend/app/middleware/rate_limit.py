"""Rate limiting middleware using SlowAPI."""

from slowapi import Limiter
from slowapi.util import get_remote_address


# Create rate limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],  # Global default
    storage_uri="memory://",  # Use memory storage (upgrade to Redis for production)
)
