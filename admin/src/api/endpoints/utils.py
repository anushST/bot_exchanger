from datetime import datetime, timedelta
from enum import Enum


class PeriodEnum(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


def get_period_range(period: PeriodEnum):
    now = datetime.utcnow()
    if period == PeriodEnum.day:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == PeriodEnum.week:
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(weeks=1)
    elif period == PeriodEnum.month:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = start.replace(day=28) + timedelta(days=4)
        end = next_month.replace(day=1)
    else:  # PeriodEnum.year
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1)
    return start, end
