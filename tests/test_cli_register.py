import shlex

import health_data_connect.cli as cli


def test_register_invokes_claude(monkeypatch):
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"] = cmd

        class R:
            returncode = 0

        return R()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["register"])
    assert rc == 0
    assert seen["cmd"] == shlex.split(cli.REGISTER_CMD)


def test_register_falls_back_when_claude_missing(monkeypatch, capsys):
    def fake_run(cmd, **kw):
        raise FileNotFoundError("claude")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    rc = cli.main(["register"])
    assert rc == 0
    assert cli.REGISTER_CMD in capsys.readouterr().out
