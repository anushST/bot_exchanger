import math
from datetime import datetime


def difference_in_minutes(start_time: datetime, end_time: datetime) -> int:
    """Find difference between to periods of time in minutes rounded up."""
    delta = end_time - start_time
    minutes = delta.total_seconds() / 60
    return math.ceil(minutes)
