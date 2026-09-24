# health-data-connect

## What this is
A small MCP server that talks **directly to the Google Health API**, letting anyone connect their
Fitbit/Google-Health data to a local MCP client with one command and **no OAuth client id/secret
of their own**. It is NOT a hosted service: no server, no token storage — tokens live only on each
user's machine. Not a wrapper around another package (we build on the API directly).

## Structure
- `src/health_data_connect/config.py` — paths, scopes (sleep + activity, read-only), API base.
- `src/health_data_connect/client.py` — `ensure_client()`: drops the embedded public Desktop
  client into the config dir if absent (never clobbers a user's own).
- `src/health_data_connect/auth.py` — OAuth2 PKCE flow, token store, `refresh_token()`, `run_setup()`.
- `src/health_data_connect/api.py` — `google_get`/`google_post`, paged `list_data_points`, `daily_roll_up`.
- `src/health_data_connect/health.py` — `parse_range`, `get_sleep`, `get_activity` (normalized).
- `src/health_data_connect/server.py` — FastMCP server + `get_sleep`/`get_activity` tools.
- `src/health_data_connect/cli.py` — `auth` / `serve` / `disconnect` / `register`.
- `src/health_data_connect/data/google_client.json` — embedded public Desktop client (committed;
  operator replaces placeholders before publish — see `docs/operator-setup.md`).
- `tests/` — pytest, one file per unit. `site/` — homepage + privacy for OAuth verification.
- `docs/` — spec, plan, decisions, launch-checklist, operator-setup.

## How to work here
- **Add a metric:** add its data-type spelling + extractor in `health.py` (see `_ACTIVITY_SOURCES`
  and `get_sleep`), then a tool in `server.py`. TDD with mocked `api.*` (see `tests/test_health.py`).
- **Auth:** `auth` = `ensure_client()` → `auth.run_setup()`. `serve` = `ensure_client()` → `server.run_server()`.
- **Never** read, print, or log token/health payloads.
- Numbers from the API arrive as JSON strings — always cast; absent ≠ zero.

## Gotchas
- Requires Python **3.11+**; `.python-version` pins 3.11 for `uv`.
- Pinned to **`mcp<2`** (FastMCP API). TODO: migrate to mcp 2.x (`MCPServer`).
- Live testing needs the operator to embed real client credentials first (placeholders ship in git).

## Verification
- `uv run pytest` — full suite must be green.
- Live: `uv run health-data-connect auth`, then ask Claude "How did I sleep last week?".
