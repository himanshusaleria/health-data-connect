from datetime import date

from health_data_connect import api, health


def test_parse_range_explicit():
    start, end = health.parse_range("2026-01-01", "2026-01-07")
    assert start == date(2026, 1, 1)
    assert end == date(2026, 1, 7)


def test_get_sleep_aggregates_one_night(monkeypatch):
    # Two sessions that both end on the night of 2026-01-05 (offset +1h).
    session = lambda asleep, deep: {
        "sleep": {
            "interval": {
                "startTime": "2026-01-04T22:00:00Z",
                "endTime": "2026-01-05T05:30:00Z",
                "endUtcOffset": "3600s",
            },
            "summary": {
                "minutesAsleep": str(asleep),
                "stagesSummary": [{"type": "DEEP", "minutes": str(deep)}],
            },
        }
    }
    monkeypatch.setattr(api, "list_data_points", lambda *a, **k: [session(200, 40), session(60, 10)])
    nights = health.get_sleep("2026-01-05", "2026-01-05")
    assert len(nights) == 1
    n = nights[0]
    assert n["date"] == "2026-01-05"
    assert n["total_minutes"] == 260
    assert n["deep_minutes"] == 50
    assert n["sessions"] == 2


def test_get_activity_assembles_days(monkeypatch):
    def fake_rollup(type_path, start, end, cap_days=90):
        civ = {"civilStartTime": {"date": {"year": 2026, "month": 1, "day": 3}}}
        return {
            "steps": [{**civ, "steps": {"countSum": "8000"}}],
            "distance": [{**civ, "distance": {"millimetersSum": "6000000"}}],
            "floors": [{**civ, "floors": {"countSum": "12"}}],
            "total-calories": [{**civ, "totalCalories": {"kcalSum": "2200"}}],
        }[type_path]

    monkeypatch.setattr(api, "daily_roll_up", fake_rollup)
    days = health.get_activity("2026-01-03", "2026-01-03")
    assert len(days) == 1
    d = days[0]
    assert d["date"] == "2026-01-03"
    assert d["steps"] == 8000
    assert d["distance_km"] == 6.0
    assert d["floors"] == 12
    assert d["calories_out"] == 2200
