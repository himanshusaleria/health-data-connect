import health_data_connect.cli as cli


def test_serve_ensures_client_then_runs_server(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "ensure_client", lambda: calls.append("ensure"))
    monkeypatch.setattr(cli, "run_server", lambda: calls.append("serve"))
    rc = cli.main(["serve"])
    assert rc == 0
    assert calls == ["ensure", "serve"]
