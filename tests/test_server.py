import asyncio
import json

from health_data_connect import health, server
from health_data_connect.auth import TokenError


def test_sleep_report_formats(monkeypatch):
    monkeypatch.setattr(health, "get_sleep", lambda s, e: [{"date": "2026-01-05", "total_minutes": 260}])
    out = json.loads(server.sleep_report("2026-01-05", "2026-01-05"))
    assert out["count"] == 1
    assert out["sleep"][0]["total_minutes"] == 260


def test_sleep_report_no_data(monkeypatch):
    monkeypatch.setattr(health, "get_sleep", lambda s, e: [])
    out = json.loads(server.sleep_report(None, None))
    assert "message" in out


def test_report_surfaces_auth_error(monkeypatch):
    def boom(s, e):
        raise TokenError("Run: health-data-connect auth")

    monkeypatch.setattr(health, "get_activity", boom)
    out = json.loads(server.activity_report(None, None))
    assert "auth" in out["error"].lower()


def test_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert {"get_sleep", "get_activity"} <= names
