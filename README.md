# health-data-connect

Connect your **Fitbit / Google Health** data to a local MCP client (Claude Code, Claude
Desktop) in one command — **without creating your own Google OAuth client id or secret**.

It's a small MCP server that talks **directly to the Google Health API**. It ships one shared
Google *Desktop* OAuth client, so you just consent in your browser; your tokens and data stay
**on your machine** — this project runs no server and never receives your data.

First slice of metrics: **sleep** and **activity** (steps, distance, floors, calories). More to come.

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) installed (provides `uvx`). Python 3.11+ is handled for you.

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

You are granting **read-only** access to *your own* health data. Tokens are written only to
`~/.config/health-data-connect/` on your machine. We never see them.

## Register with Claude Code

Run the line `auth` printed, or:

```bash
uvx health-data-connect register
```

which runs `claude mcp add -s user health-data-connect -- uvx health-data-connect serve`.
If `claude` isn't on your PATH, `register` prints the command for you to run manually.

## Use it

In Claude Code:

> How did I sleep last week?
> How active was I over the last month?

Claude calls the `get_sleep` / `get_activity` tools and answers from your real data.

## Disconnect

```bash
uvx health-data-connect disconnect
```

Deletes the local token file and prints the Google revoke link
(<https://myaccount.google.com/permissions>).

## Notes & limits

- **≤100 users** while the app is unverified (Google's cap for restricted health scopes). The
  warning disappears once app verification completes.
- Reads Fitbit data via the **Google Health API** — the successor to the legacy Fitbit Web API.
- Commands: `auth`, `serve`, `register`, `disconnect`.
