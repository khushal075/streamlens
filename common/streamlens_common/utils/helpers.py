import uuid
from datetime import datetime, timezone

def generate_event_id() -> str:
    """Generates a unique ID for logs and batches."""
    return str(uuid.uuid4())

def get_current_utc() -> str:
    """Returns a standardized ISO-8601 UTC string."""
    return datetime.now(timezone.utc).isoformat()

def get_utc_now() -> datetime:
    """Returns a native datetime object (kept for backward compatibility)."""
    return datetime.now(timezone.utc)

def sanitize_string(text: str) -> str:
    """Basic cleanup for incoming raw log strings."""
    return text.strip()