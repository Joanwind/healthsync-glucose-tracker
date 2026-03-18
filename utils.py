from datetime import datetime

def parse_yyyy_mm_dd(s: str):
    """Return date string YYYY-MM-DD if valid else None."""
    try:
        return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return None