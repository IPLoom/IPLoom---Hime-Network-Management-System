from datetime import datetime, timezone

def now() -> datetime:
    """Returns the current time in UTC."""
    return datetime.now(timezone.utc)

def parse_iso_utc(iso_str: str) -> datetime:
    """Parses an ISO 8601 string and ensures it is UTC-aware."""
    if not iso_str:
        return now()
    
    # Handle 'Z' suffix and other ISO variations
    try:
        # Python 3.11+ supports 'Z' natively in fromisoformat
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return now()

def format_iso(dt: datetime) -> str:
    """Formats a datetime object to ISO 8601 string with UTC offset."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
