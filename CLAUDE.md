# health-data-connect

## What this is
A thin PyPI wrapper around `google-health-mcp` that lets anyone connect their Fitbit/Google-Health
data to a local MCP client with one command and **no OAuth client id/secret of their own**.
It is NOT a hosted service: it runs no server, stores no one's tokens, and holds no health data —
tokens live only on each user's machine.

## Structure
- `src/health_data_connect/cli.py` — CLI: `auth`, `serve`, `disconnect`, `register`.
- `src/health_data_connect/client.py` — `ensure_client()`: drops the embedded Desktop client into
  `google-health-mcp`'s config dir if absent (never clobbers a user's own).
- `src/health_data_connect/data/google_client.json` — the shared **public Desktop** OAuth client
  (committed on purpose; operator replaces placeholders before publish — see `docs/operator-setup.md`).
- `tests/` — pytest, one file per unit.
- `site/` — static homepage + privacy policy for OAuth verification.
- `docs/superpowers/` — spec and implementation plan. `docs/operator-setup.md` — Google Cloud setup.

## How to work here
- **Add/change a CLI command:** write the failing test in `tests/test_cli_*.py` first, then extend
  `cli.py` (register the subparser + dispatch). Keep delegating to `google-health-mcp`; don't fork it.
- **Auth flow:** `auth` = `ensure_client()` → `google_health_mcp.auth.setup_google_auth()`.
  `serve` = `ensure_client()` → `google_health_mcp.cli.mcp.run(transport="stdio")`.
- **Never** read, print, or log token/health payloads.

## Gotchas
- Requires Python **3.13+** (google-health-mcp's floor). `.python-version` pins it for `uv`.

## Verification
- `uv run pytest` — full suite must be green.
- Live check: `uv run health-data-connect auth`, then ask Claude "How did I sleep last week?" and
  confirm a real answer.
