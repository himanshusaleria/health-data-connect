"""Fetch and normalize sleep + activity from the Google Health API.

Notes on the API's shape (each easy to get subtly wrong):
- integers arrive as JSON strings, so every number is cast explicitly;
- a quantity that was not measured is absent, not zero;
- sleep is binned by when the night ended *locally*, from a UTC instant + offset.
"""

from datetime import date, datetime, timedelta

from . import api

_SLEEP_STAGE_COLUMNS = {
    "DEEP": "deep_minutes",
    "LIGHT": "light_minutes",
    "REM": "rem_minutes",
    "AWAKE": "wake_minutes",
}


def _num(value, cast):
    if value is None or isinstance(value, bool):
        return None
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def parse_range(start_date: str | None, end_date: str | None, default_days: int = 30) -> tuple[date, date]:
    """Inclusive [start, end] dates from ISO strings, defaulting to the last N days."""
    end = date.fromisoformat(end_date) if end_date else date.today()
    start = date.fromisoformat(start_date) if start_date else end - timedelta(days=default_days)
    return start, end


def _local_date(timestamp: str | None, offset: str | None) -> str | None:
    """Calendar date a UTC instant falls on in the user's own time (from a "3600s" offset)."""
    if not timestamp:
        return None
    try:
        moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    seconds = 0 if offset is None else _num(str(offset).rstrip("s"), int)
    if seconds is None:
        return None
    return (moment + timedelta(seconds=seconds)).date().isoformat()


def get_sleep(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """One entry per night (duration + stage breakdown), aggregating fragmented sessions."""
    start, end = parse_range(start_date, end_date)
    points = api.list_data_points(
        "sleep", "sleep.interval.civil_end_time", start, end + timedelta(days=1), page_size=25
    )
    nights: dict[str, dict] = {}
    for point in points:
        payload = point.get("sleep")
        if not isinstance(payload, dict):
            continue
        interval = payload.get("interval") or {}
        night = _local_date(interval.get("endTime"), interval.get("endUtcOffset"))
        if night is None:
            continue
        summary = payload.get("summary") or {}
        acc = nights.setdefault(night, {"date": night, "sessions": 0})
        acc["sessions"] += 1
        for field, column in (("minutesAsleep", "total_minutes"), ("minutesInSleepPeriod", "sleep_period_minutes")):
            value = _num(summary.get(field), int)
            if value is not None:
                acc[column] = acc.get(column, 0) + value
        for stage in summary.get("stagesSummary") or []:
            column = _SLEEP_STAGE_COLUMNS.get(stage.get("type"))
            minutes = _num(stage.get("minutes"), int)
            if column and minutes is not None:
                acc[column] = acc.get(column, 0) + minutes
    return [nights[day] for day in sorted(nights)]


def _rollup_day(point: dict) -> str | None:
    parts = ((point or {}).get("civilStartTime") or {}).get("date") or {}
    try:
        return f"{parts['year']:04d}-{parts['month']:02d}-{parts['day']:02d}"
    except (KeyError, TypeError, ValueError):
        return None


def _km(value):
    mm = _num(value, float)
    return None if mm is None else round(mm / 1_000_000, 6)


def _kcal(value):
    k = _num(value, float)
    return None if k is None else int(k)


#: (type_path, response field, value extractor, output column, rollup cap days)
_ACTIVITY_SOURCES = (
    ("steps", "steps", lambda p: _num(p.get("countSum"), int), "steps", 90),
    ("distance", "distance", lambda p: _km(p.get("millimetersSum")), "distance_km", 90),
    ("floors", "floors", lambda p: _num(p.get("countSum"), int), "floors", 90),
    ("total-calories", "totalCalories", lambda p: _kcal(p.get("kcalSum")), "calories_out", 14),
)


def get_activity(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """One entry per day: steps, distance (km), floors, calories out."""
    start, end = parse_range(start_date, end_date)
    end_exclusive = end + timedelta(days=1)
    days: dict[str, dict] = {}
    for type_path, field, extract, column, cap in _ACTIVITY_SOURCES:
        for point in api.daily_roll_up(type_path, start, end_exclusive, cap_days=cap):
            day = _rollup_day(point)
            payload = point.get(field)
            if day is None or not isinstance(payload, dict):
                continue
            value = extract(payload)
            # All four sources are Google "true-zero" types: a present point with
            # the value field omitted is a measured zero, not missing data.
            days.setdefault(day, {"date": day})[column] = value if value is not None else 0
    return [days[day] for day in sorted(days)]
