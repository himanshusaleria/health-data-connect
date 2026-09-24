import shlex

import health_data_connect.cli as cli
from health_data_connect import config


def test_auth_ensures_client_then_setup(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(cli, "ensure_client", lambda: calls.append("ensure"))
    monkeypatch.setattr(cli, "run_setup", lambda: calls.append("setup"))
    rc = cli.main(["auth"])
    assert rc == 0
    assert calls == ["ensure", "setup"]
    assert cli.REGISTER_CMD in capsys.readouterr().out


def test_auth_reports_token_error(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ensure_client", lambda: None)

    def boom():
        raise cli.TokenError("denied")

    monkeypatch.setattr(cli, "run_setup", boom)
    rc = cli.main(["auth"])
    assert rc == 1
    assert "denied" in capsys.readouterr().err


def test_serve_ensures_then_runs(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "ensure_client", lambda: calls.append("ensure"))
    monkeypatch.setattr(cli, "run_server", lambda: calls.append("serve"))
    rc = cli.main(["serve"])
    assert rc == 0
    assert calls == ["ensure", "serve"]


def test_disconnect_removes_tokens_and_prints_link(tmp_path, monkeypatch, capsys):
    tok = tmp_path / "google_tokens.json"
    tok.write_text("{}")
    monkeypatch.setattr(config, "GOOGLE_TOKENS_PATH", tok)
    rc = cli.main(["disconnect"])
    assert rc == 0
    assert not tok.exists()
    assert "myaccount.google.com/permissions" in capsys.readouterr().out


def test_register_invokes_claude(monkeypatch):
    seen = {}
    monkeypatch.setattr(cli.subprocess, "run", lambda cmd, **k: seen.update(cmd=cmd))
    rc = cli.main(["register"])
    assert rc == 0
    assert seen["cmd"] == shlex.split(cli.REGISTER_CMD)


def test_register_falls_back_when_claude_missing(monkeypatch, capsys):
    def boom(cmd, **k):
        raise FileNotFoundError("claude")

    monkeypatch.setattr(cli.subprocess, "run", boom)
    rc = cli.main(["register"])
    assert rc == 0
    assert cli.REGISTER_CMD in capsys.readouterr().out
