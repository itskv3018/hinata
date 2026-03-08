# utils/helpers.py
# Shared utility functions.

import re
import time
from functools import wraps


def timer(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"  ⏱️ {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper


def sanitize_input(text: str) -> str:
    """Remove potentially dangerous characters from user input."""
    # Remove null bytes and control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Limit length
    return text[:2000]


def truncate(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length, adding '...' if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_timestamp(iso_string: str) -> str:
    """Format an ISO timestamp into a human-readable string."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%b %d, %Y at %I:%M %p")
    except (ValueError, TypeError):
        return iso_string
