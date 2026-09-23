# health-data-connect Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a thin PyPI package `health-data-connect` that lets anyone connect their Fitbit/Google-Health data to a local MCP client with one command and no OAuth client id/secret of their own.

**Architecture:** A thin CLI wrapper that depends on `google-health-mcp` (imported, not forked). It ships one shared Google *Desktop* OAuth client as package data, drops it into `google-health-mcp`'s config dir when absent, then delegates auth and serving to the upstream package. Tokens live only on the user's machine; we host nothing.

**Tech Stack:** Python ≥3.11, hatchling build backend, `google-health-mcp` dependency, `argparse` CLI, `pytest`, `importlib.resources` for bundled data, `uv`/`uvx` for run+publish.

**Spec:** `docs/superpowers/specs/2026-09-23-health-data-connect-design.md`

## Global Constraints

- Package import name: `health_data_connect`; distribution + console-script + MCP-registration name: `health-data-connect`. Src layout: `src/health_data_connect/`.
- `requires-python = ">=3.11"`. Depend on `google-health-mcp` (a runtime dependency; never vendor/fork its code).
- The embedded client at `src/health_data_connect/data/google_client.json` is a **public Desktop client** — it IS committed. User tokens (`google_tokens.json`) are NEVER committed and NEVER read/logged by us.
- Integration point is exactly three upstream symbols; do not modify upstream: `google_health_mcp.config.GOOGLE_CLIENT_PATH`, `google_health_mcp.config.GOOGLE_TOKENS_PATH`, `google_health_mcp.auth.setup_google_auth()` / `google_health_mcp.auth.TokenRefused`, plus `google_health_mcp.cli.mcp` for serving.
- Never print or log health data anywhere in this package.
- The bundled client MUST NOT ship with placeholder values — a release guard (Task 9) blocks publishing a build whose `client_id` contains `REPLACE_WITH`.

## Review Focus

- **User already has their own `google_client.json`** in the config dir (prior `google-health-mcp` user) → we must NOT overwrite it. (Test in Task 2.)
- **User denies consent / `TokenRefused`** during `auth` → exit non-zero with the upstream message, no traceback. (Test in Task 3.)
- **`claude` CLI not on PATH** when running `register` → print copy-paste manual instructions, exit 0, don't crash. (Test in Task 6.)
- **`disconnect` with no token file present** → succeed idempotently and still print the revoke link. (Test in Task 5.)
- **A build with placeholder client credentials reaching users** → release guard fails the publish. (Test in Task 9.)

---

## Task 0 (OPERATOR — manual, blocks live integration + publish, NOT the coding tasks)

**Owner:** Himanshu. Agentic executors cannot do this; do Tasks 1–8 in parallel and treat this as a gate before Task 9.

**Files:** `docs/operator-setup.md` (written in Task 7) is the checklist source of truth.

- [ ] Create a Google Cloud project; enable the **Health API**.
- [ ] Configure the **OAuth consent screen**: External; add the read-only `googlehealth.*` scopes; set app name, logo, support email, homepage URL, privacy-policy URL (from Task 8's `site/`). Publish to **Production** (unverified for now).
- [ ] Create an **OAuth client → type Desktop app**. Download its JSON.
- [ ] Copy the two real values (`client_id`, `client_secret`) into `src/health_data_connect/data/google_client.json`, replacing the placeholders.
- [ ] Authorize one real Google account that has real Fitbit data; **record the authorization date** (needed to confirm >7-day refresh-token durability at the Task 9 gate).

---

## Task 1: Project scaffold + packaging

**Files:**
- Create: `pyproject.toml`
- Create: `src/health_data_connect/__init__.py`
- Create: `tests/test_smoke.py`

**Interfaces:**
- Produces: importable package `health_data_connect` with `__version__: str`; console script `health-data-connect` → `health_data_connect.cli:main` (cli added in Task 3; scaffold points at it now).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_smoke.py
import importlib

def test_package_imports_and_has_version():
    pkg = importlib.import_module("health_data_connect")
    assert isinstance(pkg.__version__, str)
    assert pkg.__version__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_smoke.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'health_data_connect'`

- [ ] **Step 3: Write `pyproject.toml` and the package**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "health-data-connect"
version = "0.1.0"
description = "Connect your Fitbit/Google Health data to a local MCP client in one command — no OAuth client id/secret of your own."
requires-python = ">=3.11"
dependencies = ["google-health-mcp"]

[project.scripts]
health-data-connect = "health_data_connect.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/health_data_connect"]

[tool.hatch.build.targets.wheel.force-include]
"src/health_data_connect/data/google_client.json" = "health_data_connect/data/google_client.json"
```

```python
# src/health_data_connect/__init__.py
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("health-data-connect")
except PackageNotFoundError:  # running from source before install
    __version__ = "0.0.0"
```

- [ ] **Step 4: Install and run the test**

Run: `uv venv && uv pip install -e . && uv run pytest tests/test_smoke.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/health_data_connect/__init__.py tests/test_smoke.py
git commit -m "feat: scaffold health-data-connect package"
```

---

## Task 2: `ensure_client()` — place the embedded client without clobbering

**Files:**
- Create: `src/health_data_connect/data/google_client.json` (placeholder values)
- Create: `src/health_data_connect/client.py`
- Create: `tests/test_client.py`

**Interfaces:**
- Produces: `ensure_client() -> Path` — if `google_health_mcp.config.GOOGLE_CLIENT_PATH` is absent, writes the bundled client JSON there (mode 0600, parents created) and returns the path; if present, returns it untouched.

- [ ] **Step 1: Create the placeholder bundled client**

```json
{
  "installed": {
    "client_id": "REPLACE_WITH_REAL_CLIENT_ID.apps.googleusercontent.com",
    "client_secret": "REPLACE_WITH_REAL_CLIENT_SECRET",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token"
  }
}
```

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_client.py
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
```

- [ ] **Step 3: Run to verify it fails**

Run: `uv run pytest tests/test_client.py -v`
Expected: FAIL — `AttributeError: module 'health_data_connect.client' has no attribute 'config'`

- [ ] **Step 4: Implement `client.py`**

```python
# src/health_data_connect/client.py
"""Place our shared, public Desktop OAuth client where google-health-mcp reads it."""
import os
from importlib.resources import files
from pathlib import Path

from google_health_mcp import config


def _bundled_client_bytes() -> bytes:
    return files("health_data_connect").joinpath("data/google_client.json").read_bytes()


def ensure_client() -> Path:
    target = Path(config.GOOGLE_CLIENT_PATH)
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, _bundled_client_bytes())
    finally:
        os.close(fd)
    return target
```

- [ ] **Step 5: Run to verify it passes**

Run: `uv run pytest tests/test_client.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/health_data_connect/client.py src/health_data_connect/data/google_client.json tests/test_client.py
git commit -m "feat: ensure_client places bundled Desktop client without clobbering"
```

---

## Task 3: `cli` with the `auth` subcommand

**Files:**
- Create: `src/health_data_connect/cli.py`
- Create: `tests/test_cli_auth.py`

**Interfaces:**
- Consumes: `ensure_client()` (Task 2); `google_health_mcp.auth.setup_google_auth`, `google_health_mcp.auth.TokenRefused`.
- Produces: `main(argv: list[str] | None = None) -> int`; subcommand `auth` runs `ensure_client()` then `setup_google_auth()`, prints the registration line on success, and on `TokenRefused` prints the message to stderr and returns 1. Registration line constant `REGISTER_CMD = "claude mcp add -s user health-data-connect -- uvx health-data-connect serve"`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli_auth.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_auth.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'health_data_connect.cli'`

- [ ] **Step 3: Implement `cli.py` (auth only for now)**

```python
# src/health_data_connect/cli.py
"""health-data-connect CLI: auth | serve | disconnect | register."""
import argparse
import sys

from google_health_mcp.auth import TokenRefused, setup_google_auth

from .client import ensure_client

REGISTER_CMD = "claude mcp add -s user health-data-connect -- uvx health-data-connect serve"


def _cmd_auth() -> int:
    ensure_client()
    try:
        setup_google_auth()
    except TokenRefused as e:
        print(e, file=sys.stderr)
        return 1
    print("\nConnected. Register with your MCP client:\n  " + REGISTER_CMD)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="health-data-connect")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    sub.add_parser("auth", help="Connect your Google/Fitbit account (browser consent)")
    args = parser.parse_args(argv)
    if args.cmd == "auth":
        return _cmd_auth()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_cli_auth.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/health_data_connect/cli.py tests/test_cli_auth.py
git commit -m "feat: add auth subcommand delegating to google-health-mcp"
```

---

## Task 4: `serve` subcommand

**Files:**
- Modify: `src/health_data_connect/cli.py`
- Create: `tests/test_cli_serve.py`

**Interfaces:**
- Consumes: `ensure_client()`; `google_health_mcp.cli.mcp` (importing `google_health_mcp.cli` registers all tools as a side effect).
- Produces: subcommand `serve` runs `ensure_client()` then `run_server()`, which calls `mcp.run(transport="stdio")`. `run_server()` is a seam so tests don't start a real server.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_serve.py
import health_data_connect.cli as cli

def test_serve_ensures_client_then_runs_server(monkeypatch):
    calls = []
    monkeypatch.setattr(cli, "ensure_client", lambda: calls.append("ensure"))
    monkeypatch.setattr(cli, "run_server", lambda: calls.append("serve"))
    rc = cli.main(["serve"])
    assert rc == 0
    assert calls == ["ensure", "serve"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_serve.py -v`
Expected: FAIL — `AttributeError: module 'health_data_connect.cli' has no attribute 'run_server'`

- [ ] **Step 3: Implement `serve`**

Add to `cli.py`:

```python
def run_server() -> None:
    # Importing the upstream cli registers every tool on its shared `mcp` instance.
    from google_health_mcp.cli import mcp
    mcp.run(transport="stdio")


def _cmd_serve() -> int:
    ensure_client()
    run_server()
    return 0
```

Register the subparser (`sub.add_parser("serve", help="Run the MCP server (stdio)")`) and dispatch `elif args.cmd == "serve": return _cmd_serve()`.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_cli_serve.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/health_data_connect/cli.py tests/test_cli_serve.py
git commit -m "feat: add serve subcommand delegating to upstream MCP server"
```

---

## Task 5: `disconnect` subcommand

**Files:**
- Modify: `src/health_data_connect/cli.py`
- Create: `tests/test_cli_disconnect.py`

**Interfaces:**
- Consumes: `google_health_mcp.config.GOOGLE_TOKENS_PATH`.
- Produces: subcommand `disconnect` deletes the local tokens file if present (idempotent) and prints the Google revoke link `https://myaccount.google.com/permissions`. Returns 0 whether or not a file existed.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli_disconnect.py
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_disconnect.py -v`
Expected: FAIL — argparse rejects `disconnect` (invalid choice) → SystemExit

- [ ] **Step 3: Implement `disconnect`**

Add to `cli.py`:

```python
from pathlib import Path
from google_health_mcp import config

REVOKE_URL = "https://myaccount.google.com/permissions"


def _cmd_disconnect() -> int:
    tokens = Path(config.GOOGLE_TOKENS_PATH)
    tokens.unlink(missing_ok=True)
    print(f"Local tokens removed. Also revoke access at: {REVOKE_URL}")
    return 0
```

Register `sub.add_parser("disconnect", help="Delete local tokens and show the revoke link")` and dispatch it.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_cli_disconnect.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/health_data_connect/cli.py tests/test_cli_disconnect.py
git commit -m "feat: add disconnect subcommand (local wipe + revoke link)"
```

---

## Task 6: `register` subcommand

**Files:**
- Modify: `src/health_data_connect/cli.py`
- Create: `tests/test_cli_register.py`

**Interfaces:**
- Produces: subcommand `register` runs `REGISTER_CMD` via `subprocess.run(shlex.split(REGISTER_CMD))`. If the `claude` executable is not found (`FileNotFoundError`), print the manual command and return 0.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli_register.py
import shlex
import health_data_connect.cli as cli

def test_register_invokes_claude(monkeypatch):
    seen = {}
    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        class R: returncode = 0
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
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_register.py -v`
Expected: FAIL — argparse rejects `register`

- [ ] **Step 3: Implement `register`**

Add to `cli.py` (add `import shlex`, `import subprocess` at top):

```python
def _cmd_register() -> int:
    try:
        subprocess.run(shlex.split(REGISTER_CMD))
    except FileNotFoundError:
        print("`claude` not found. Register manually with:\n  " + REGISTER_CMD)
    return 0
```

Register `sub.add_parser("register", help="Register this server with Claude Code")` and dispatch it.

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_cli_register.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/health_data_connect/cli.py tests/test_cli_register.py
git commit -m "feat: add register subcommand with claude-missing fallback"
```

---

## Task 7: Docs — README, operator setup, project CLAUDE.md

**Files:**
- Create: `README.md`
- Create: `docs/operator-setup.md`
- Create: `CLAUDE.md`
- Create: `tests/test_docs.py`

**Interfaces:** none (documentation). One guard test keeps the critical warning-screen walkthrough and the placeholder-swap step from silently disappearing.

- [ ] **Step 1: Write the failing guard test**

```python
# tests/test_docs.py
from pathlib import Path

def test_readme_covers_unverified_warning():
    txt = Path("README.md").read_text()
    assert "unverified" in txt.lower()
    assert "Advanced" in txt  # the click-through path users get stuck on
    assert "uvx health-data-connect auth" in txt

def test_operator_setup_flags_placeholder_swap():
    txt = Path("docs/operator-setup.md").read_text()
    assert "REPLACE_WITH_REAL_CLIENT_ID" in txt
    assert "Desktop app" in txt
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_docs.py -v`
Expected: FAIL — `FileNotFoundError: 'README.md'`

- [ ] **Step 3: Write the docs**

`README.md` covers: what it is; prerequisite (`uv` installed); the one-liner `uvx health-data-connect auth`; a step-by-step of the Google **"unverified app"** screen (**Advanced → Go to health-data-connect (unsafe) → choose account → Allow**), stating it grants read-only access to your own data and tokens stay on your machine; the `register` step; an example question to ask Claude; and `disconnect` to revoke.

`docs/operator-setup.md` = the Task 0 checklist verbatim, including replacing `REPLACE_WITH_REAL_CLIENT_ID` / `REPLACE_WITH_REAL_CLIENT_SECRET` in `src/health_data_connect/data/google_client.json`, the **Desktop app** client-type requirement, publishing to Production, the rotation procedure, and the §7.2 verification checklist (homepage, privacy policy, domain ownership, demo video, scope justifications, CASA — with the no-backend caveat).

`CLAUDE.md` per the global bootstrap template — sections: **What this is** (incl. what it's NOT: no server, no token storage), **Structure**, **How to work here** (the auth/serve/disconnect flows), **Gotchas** (empty), **Verification** (`uv run pytest`; live `auth` → ask Claude a sleep question).

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_docs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/operator-setup.md CLAUDE.md tests/test_docs.py
git commit -m "docs: README, operator setup, and project CLAUDE.md"
```

---

## Task 8: Verification assets — static homepage + privacy policy (`site/`)

**Files:**
- Create: `site/index.html`
- Create: `site/privacy.html`
- Create: `tests/test_site.py`

**Interfaces:** none. Static pages the OAuth consent screen and domain-ownership check link to (§7.2). Deployment (domain, hosting) is an operator step, not code.

- [ ] **Step 1: Write the failing guard test**

```python
# tests/test_site.py
from pathlib import Path

def test_privacy_states_ondevice_and_readonly():
    txt = Path("site/privacy.html").read_text().lower()
    assert "read-only" in txt
    assert "on your device" in txt or "on your machine" in txt
    assert "no server" in txt or "do not operate" in txt

def test_homepage_links_privacy():
    assert "privacy.html" in Path("site/index.html").read_text()
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_site.py -v`
Expected: FAIL — `FileNotFoundError: 'site/privacy.html'`

- [ ] **Step 3: Write the static pages**

`site/index.html`: a single self-contained page — what the app does, who it's for, a link to `privacy.html`, and a support email. `site/privacy.html`: states exactly which read-only `googlehealth.*` data is accessed, that it is read-only, that all data and tokens stay **on your device**, that we operate **no server** and never receive user data, and how to revoke (`myaccount.google.com/permissions`).

- [ ] **Step 4: Run to verify it passes**

Run: `uv run pytest tests/test_site.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add site/index.html site/privacy.html tests/test_site.py
git commit -m "feat: static homepage + privacy policy for OAuth verification"
```

---

## Task 9 (OPERATOR gate — live integration, durability check, publish)

**Owner:** Himanshu. Requires Task 0's real client embedded and Tasks 1–8 merged.

**Files:**
- Create: `tests/test_release_guard.py`

- [ ] **Step 1: Release guard — fail the build if placeholders remain**

```python
# tests/test_release_guard.py
import json, os
from importlib.resources import files
import pytest

@pytest.mark.skipif(os.environ.get("RELEASE") != "1", reason="release-only guard")
def test_bundled_client_is_real():
    data = json.loads(files("health_data_connect").joinpath("data/google_client.json").read_text())
    cid = data["installed"]["client_id"]
    assert "REPLACE_WITH" not in cid, "Refusing to publish with placeholder client credentials"
    assert cid.endswith(".apps.googleusercontent.com")
```

Run before publish: `RELEASE=1 uv run pytest tests/test_release_guard.py -v` → must PASS.

- [ ] **Step 2: Live end-to-end** — on a real machine: `uv run health-data-connect auth`, click through consent, `health-data-connect register`, then in Claude Code ask *"How did I sleep last week?"* and confirm a real answer.
- [ ] **Step 3: Durability gate (§9.1)** — confirm the refresh token is still valid **>7 days** after the Task 0 authorization date (or confirm via Google docs that unverified-production tokens don't carry the Testing-mode 7-day expiry). **If tokens expire at 7 days, STOP — the one-time-consent UX is broken; revisit the design before public launch.**
- [ ] **Step 4: Publish** — `RELEASE=1 uv run pytest` (full suite) green, then `uvx --from build pyproject-build` (or `uv build`) and publish to PyPI. Tag the release.
- [ ] **Step 5: Verification track (parallel, §7.2)** — deploy `site/`, verify domain ownership, record the demo video, submit scope justifications + CASA. Lifts the 100-user cap and removes the warning.

---

## Self-Review

- **Spec coverage:** §1/§4 architecture → Tasks 2–4; §5 CLI (auth/serve/disconnect/register) → Tasks 3–6; §6 onboarding UX → Task 7 README; §7.1 operator base → Task 0 + Task 7; §7.2 verification → Tasks 8, 9.5; §8 security (on-device, no logging, disconnect) → Tasks 2/5/7; §9.1 durability gate → Task 9.3; §10 milestones → Task ordering. Covered.
- **Placeholder scan:** no TODO/TBD; every code step has real code. The intentional `REPLACE_WITH_*` strings are product placeholders guarded by Task 9.1, not plan placeholders.
- **Type consistency:** `ensure_client`, `run_server`, `REGISTER_CMD`, `REVOKE_URL`, `main(argv)` names are used identically across Tasks 2–6.
- **Review Focus:** all five lines have owning tests (Tasks 2, 3, 5, 6, 9).
