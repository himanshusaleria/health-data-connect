# health-data-connect

Connect your **Fitbit / Google Health** data to a local MCP client (Claude Code, Claude
Desktop) in one command — **without creating your own Google OAuth client id or secret**.

It's a thin wrapper around [`google-health-mcp`](https://pypi.org/project/google-health-mcp/):
it ships one shared Google *Desktop* OAuth client, drops it into place, and runs the browser
consent for you. Your tokens and health data stay **on your machine** — this project runs no
server and never receives your data.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed (provides `uvx`). That's it — `uvx` fetches
  everything else on demand.

## Connect (one command)

```bash
uvx health-data-connect auth
```

A browser opens. Because this is a small personal app, Google shows a
**"Google hasn't verified this app"** screen. This is expected. To continue:

1. Click **Advanced**.
2. Click **Go to health-data-connect (unsafe)**.
3. Choose the Google account that has your Fitbit data.
4. Click **Allow**.

You are granting **read-only** access to *your own* health data, and the resulting tokens are
written only to your machine (`~/.config/google-health-mcp/`). We never see them.

When it finishes you'll see `Tokens saved` and a registration command.

## Register with Claude Code

Run the line `auth` printed, or:

```bash
uvx health-data-connect register
```

which runs:

```bash
claude mcp add -s user health-data-connect -- uvx health-data-connect serve
```

If `claude` isn't on your PATH, `register` prints that command for you to run manually.

## Use it

In Claude Code, ask a question that needs your data, e.g.:

> How did I sleep last week?

Claude will call the health tools (`health_get_sleep`, `health_get_activity`,
`health_get_heart_rate`, …) and answer from your real data.

## Disconnect

```bash
uvx health-data-connect disconnect
```

This deletes the local token file and prints the Google revoke link
(<https://myaccount.google.com/permissions>) so you can fully revoke access.

## Notes & limits

- **≤100 users** while the app is unverified (Google's cap for restricted health scopes). The
  "unverified app" warning disappears once app verification completes.
- Reads Fitbit data via the **Google Health API** — the successor to the legacy Fitbit Web API.
- Commands: `auth`, `serve`, `register`, `disconnect`.
