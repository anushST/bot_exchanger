from datetime import datetime, timedelta


def get_period_range(period: str):
    """
    Возвращает кортеж (start_datetime, end_datetime) для выбранного периода.
    Период: "day", "week", "month", "year".
    """
    now = datetime.now()

    if period == "day":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)

    elif period == "week":
        # Предположим, неделя начинается в понедельник
        start = now - timedelta(days=now.weekday())
        start = datetime(start.year, start.month, start.day)
        end = start + timedelta(weeks=1)

    elif period == "month":
        start = datetime(now.year, now.month, 1)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)

    elif period == "year":
        # Период: календарный год
        start = datetime(now.year, 1, 1)
        end = datetime(now.year + 1, 1, 1)

    else:
        # По умолчанию пусть будет день
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)

    return start, end
