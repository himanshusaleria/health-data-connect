from datetime import date

from health_data_connect import api


def test_build_filter_closed_range():
    f = api.build_filter("sleep.interval.civil_end_time", date(2026, 1, 1), date(2026, 1, 8))
    assert f == 'sleep.interval.civil_end_time >= "2026-01-01" AND sleep.interval.civil_end_time < "2026-01-08"'


def test_google_get_sends_bearer_token(monkeypatch):
    seen = {}

    def fake_get_json(url, headers):
        seen["url"] = url
        seen["headers"] = headers
        return {"ok": True}

    monkeypatch.setattr(api, "refresh_token", lambda: "TOK")
    monkeypatch.setattr(api, "_get_json", fake_get_json)
    out = api.google_get("users/me/dataTypes/sleep/dataPoints", {"pageSize": 25})
    assert out == {"ok": True}
    assert seen["headers"]["Authorization"] == "Bearer TOK"
    assert "users/me/dataTypes/sleep/dataPoints?pageSize=25" in seen["url"]


def test_list_data_points_follows_pages(monkeypatch):
    calls = []

    def fake_google_get(path, params):
        calls.append(params.get("pageToken"))
        if "pageToken" not in params:
            return {"dataPoints": [{"a": 1}], "nextPageToken": "T2"}
        return {"dataPoints": [{"a": 2}]}

    monkeypatch.setattr(api, "google_get", fake_google_get)
    pts = api.list_data_points("sleep", "sleep.interval.civil_end_time", date(2026, 1, 1), date(2026, 1, 8))
    assert pts == [{"a": 1}, {"a": 2}]
    assert calls == [None, "T2"]  # first page has no token, second replays T2


def test_list_data_points_empty_page_with_token_keeps_going(monkeypatch):
    def fake_google_get(path, params):
        if "pageToken" not in params:
            return {"dataPoints": [], "nextPageToken": "T2"}  # empty but more behind it
        return {"dataPoints": [{"a": 9}]}

    monkeypatch.setattr(api, "google_get", fake_google_get)
    pts = api.list_data_points("sleep", "sleep.interval.civil_end_time", date(2026, 1, 1), date(2026, 1, 8))
    assert pts == [{"a": 9}]
