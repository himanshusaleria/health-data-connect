# Google OAuth — restricted scope justifications

For the OAuth verification / restricted-scope review. Paste each justification into the
console's per-scope field. App type: **installed Desktop app** that runs **entirely on the
user's own device**; it operates **no backend server** and never transmits user health data
off the device.

> **Working app name:** health-data-connect (update everywhere if renamed before submission).

## Data-use summary (overarching)
health-data-connect is a local tool that lets a person query **their own** wearable health
data through their personal AI assistant (e.g. Claude), by asking natural-language questions
like "how did I sleep last week?" or "how active was I this month?". It reads the user's data
directly from the Google Health API **on the user's machine**, formats it, and hands it to the
locally-running AI client. We — the developer — never receive, store, log, or transmit the
user's health data or tokens. Access is **read-only**. Data is used solely to answer the
user's own questions, in the same session, on their device. It is never sold, shared, used
for advertising, or used to train models. Users can revoke at any time via
`disconnect` and https://myaccount.google.com/permissions.

## Scope 1 — `https://www.googleapis.com/auth/googlehealth.sleep.readonly`
**Why the app needs it:** to answer the user's questions about their own sleep, the app reads
nightly sleep records (duration, sleep-period length, and stage breakdown: deep/light/REM/
awake). This is surfaced as the `get_sleep` tool the user's AI assistant calls.
**Why read-only / minimal:** the app never writes sleep data; this is the narrowest scope that
grants read access to sleep, and no non-restricted scope exposes this data.
**Handling:** read on-device, passed to the local AI client, never sent to any server we run.

## Scope 2 — `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly`
**Why the app needs it:** to answer the user's questions about their own activity, the app
reads daily activity aggregates (steps, distance, floors, calories burned). This is surfaced
as the `get_activity` tool.
**Why read-only / minimal:** the app never writes activity data; this is the narrowest scope
covering daily activity/fitness reads, and no non-restricted scope exposes it.
**Handling:** identical to above — on-device only, no server, read-only, user-revocable.

## Notes for the reviewer
- The OAuth client is a **Desktop (installed) app**; there is no web backend and no server-side
  storage of Google user data.
- Tokens are stored only in the user's local config directory (`~/.config/health-data-connect/`),
  file-permission `0600`.
- Homepage and privacy policy are served at <DOMAIN> (see `site/index.html`, `site/privacy.html`).
- Only the two scopes above are requested; more will be added (with justifications) only as new
  read-only metrics ship.
