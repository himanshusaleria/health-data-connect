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
    # Real path: a malformed/missing client file makes upstream raise TokenRefused.
    monkeypatch.setattr(cli, "ensure_client", lambda: None)

    def boom():
        raise cli.TokenRefused("bad creds")

    monkeypatch.setattr(cli, "setup_google_auth", boom)
    rc = cli.main(["auth"])
    assert rc == 1
    assert "bad creds" in capsys.readouterr().err


def test_auth_handles_consent_denial_exit(monkeypatch, capsys):
    # Real path: on consent denial/timeout upstream prints to stderr and calls
    # sys.exit(1) (raising SystemExit) rather than raising TokenRefused. The
    # wrapper must convert that into a clean non-zero return without claiming success.
    monkeypatch.setattr(cli, "ensure_client", lambda: None)

    def denied():
        raise SystemExit(1)

    monkeypatch.setattr(cli, "setup_google_auth", denied)
    rc = cli.main(["auth"])
    assert rc == 1
    assert cli.REGISTER_CMD not in capsys.readouterr().out
