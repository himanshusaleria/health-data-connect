import json

from health_data_connect import client as client_mod


def test_writes_bundled_client_when_absent(tmp_path, monkeypatch):
    target = tmp_path / "cfg" / "google_client.json"
    monkeypatch.setattr(client_mod.config, "GOOGLE_CLIENT_PATH", target)
    result = client_mod.ensure_client()
    assert result == target
    assert target.exists()
    assert oct(target.stat().st_mode)[-3:] == "600"
    assert "installed" in json.loads(target.read_text())


def test_does_not_clobber_existing_client(tmp_path, monkeypatch):
    target = tmp_path / "google_client.json"
    target.write_text('{"installed": {"client_id": "MINE"}}')
    monkeypatch.setattr(client_mod.config, "GOOGLE_CLIENT_PATH", target)
    client_mod.ensure_client()
    assert json.loads(target.read_text())["installed"]["client_id"] == "MINE"
