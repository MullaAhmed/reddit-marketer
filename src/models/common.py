"""
Shared timestamp and ID helpers.
"""

from datetime import datetime, timezone
from uuid import uuid4


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())


def get_current_timestamp() -> float:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc).timestamp()


def format_timestamp(timestamp: float) -> str:
    """Format timestamp for display."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")