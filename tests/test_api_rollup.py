from datetime import date

from health_data_connect import api


def test_daily_roll_up_posts_single_window(monkeypatch):
    seen = []

    def fake_post(path, body):
        seen.append((path, body))
        return {"rollupDataPoints": [{"x": 1}]}

    monkeypatch.setattr(api, "google_post", fake_post)
    pts = api.daily_roll_up("steps", date(2026, 1, 1), date(2026, 1, 8), cap_days=90)
    assert pts == [{"x": 1}]
    path, body = seen[0]
    assert path == "users/me/dataTypes/steps/dataPoints:dailyRollUp"
    assert body["range"]["start"] == {"date": {"year": 2026, "month": 1, "day": 1}}
    assert body["range"]["end"] == {"date": {"year": 2026, "month": 1, "day": 8}}
    assert body["windowSizeDays"] == 1


def test_daily_roll_up_chunks_by_cap(monkeypatch):
    windows = []

    def fake_post(path, body):
        windows.append((body["range"]["start"]["date"]["day"], body["range"]["end"]["date"]["day"]))
        return {"rollupDataPoints": [{"d": body["range"]["start"]["date"]["day"]}]}

    monkeypatch.setattr(api, "google_post", fake_post)
    # 20-day span, cap 14 → two chunks: [1,15) and [15,21)
    pts = api.daily_roll_up("total-calories", date(2026, 1, 1), date(2026, 1, 21), cap_days=14)
    assert windows == [(1, 15), (15, 21)]
    assert pts == [{"d": 1}, {"d": 15}]
