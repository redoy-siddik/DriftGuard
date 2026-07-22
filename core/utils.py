from django.utils import timezone
from datetime import timedelta

def get_time_range(hours=24):
    """Return timezone-aware start and end datetimes for the given number of hours ago."""
    now = timezone.now()
    start = now - timedelta(hours=hours)
    return start, now

def format_drift_severity(score):
    """Map composite drift score to human-readable status string."""
    if score >= 3.5:
        return 'critical'
    elif score >= 2.0:
        return 'warning'
    return 'normal'
