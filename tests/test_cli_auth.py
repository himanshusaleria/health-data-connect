import health_data_connect.cli as cli


def test_auth_ensures_client_then_runs_setup(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(cli, "ensure_client", lambda: calls.append("ensure"))
    monkeypatch.setattr(cli, "setup_google_auth", lambda: calls.append("setup"))
    rc = cli.main(["auth"])
    assert rc == 0
    assert calls == ["ensure", "setup"]
    assert cli.REGISTER_CMD in capsys.readouterr().out


def test_auth_reports_token_refused(monkeypatch, capsys):
    monkeypatch.setattr(cli, "ensure_client", lambda: None)

    def boom():
        raise cli.TokenRefused("bad creds")

    monkeypatch.setattr(cli, "setup_google_auth", boom)
    rc = cli.main(["auth"])
    assert rc == 1
    assert "bad creds" in capsys.readouterr().err
