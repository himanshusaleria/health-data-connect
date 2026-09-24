import health_data_connect.cli as cli
from google_health_mcp import config


def test_disconnect_removes_tokens_and_prints_link(tmp_path, monkeypatch, capsys):
    tok = tmp_path / "google_tokens.json"
    tok.write_text("{}")
    monkeypatch.setattr(config, "GOOGLE_TOKENS_PATH", tok)
    rc = cli.main(["disconnect"])
    assert rc == 0
    assert not tok.exists()
    assert "myaccount.google.com/permissions" in capsys.readouterr().out


def test_disconnect_is_idempotent_when_absent(tmp_path, monkeypatch, capsys):
    tok = tmp_path / "nope.json"
    monkeypatch.setattr(config, "GOOGLE_TOKENS_PATH", tok)
    rc = cli.main(["disconnect"])
    assert rc == 0
    assert "myaccount.google.com/permissions" in capsys.readouterr().out
