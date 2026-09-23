# Design — health-data-connect

**Status:** Draft for review · **Date:** 2026-09-23 · **Owner:** Himanshu
**Type:** Personal side project (NOT a business — see `validation-engine/.../32_wearable-ai-connector/build-plan.md`)

---

## 1. Summary

A small, distributable package that lets anyone connect their **Fitbit / Google Health
data to a local MCP client** (Claude Code, Claude Desktop) with a single command — and
**without ever creating their own Google OAuth client id or secret**.

The key realization that makes this tiny: an existing PyPI package, `google-health-mcp`,
already implements every tool and the entire Google Health API + PKCE auth flow. Its only
friction is that it makes each user supply their own `google_client.json`. We remove that
friction by **shipping one shared Google *Desktop* OAuth client embedded in our package**.
A Desktop client is a *public client* — its "secret" is non-confidential by design, and
security comes from PKCE plus a mandatory per-user browser consent. So one embedded client
serves everyone; each user just clicks "Allow" in their own Google account, and their tokens
live on their own machine.

We host nothing and hold no one's health data.

## 2. Goal & non-goals

**Goal:** A user runs `uvx health-data-connect auth`, consents in their browser, and can
immediately ask Claude Code questions about their real Fitbit data — with zero client-id/secret
setup on their part.

**Secondary goal (now in scope):** pursue **Google OAuth app verification** for the restricted
health scopes, so the app can serve **>100 users with no "unverified app" warning**. The
architecture does not change for this; it adds supporting deliverables (privacy policy, public
homepage, demo video, CASA security assessment) and a phased rollout: ship unverified first,
verify in parallel. See §7.2 and §10.

**Non-goals (explicitly out of scope):**
- No hosted OAuth broker, no server, no Cloudflare Worker, no database. (Verification is pursued
  *without* adding a backend — the on-device model is an asset here, not a blocker.)
- We never store, transmit, or see any user's health data or tokens.
- No remote MCP transport (ChatGPT / Claude.ai web connectors). Local clients only.
- No re-implementation of tools or normalization — we inherit `google-health-mcp`'s.
- No Apple Health / Garmin / Whoop / raw Fitbit Web API (dying ~Sept 2026).

## 3. Key decisions

| Choice | Decision | Why |
|---|---|---|
| Data source | **Google Health API** (`health.googleapis.com/v4`) via `google-health-mcp` | Official successor to the deprecated Fitbit Web API; the tools already exist |
| Build strategy | **Thin wrapper** that depends on `google-health-mcp`, not a fork | Inherits all tools + upstream fixes; our only job is auth ergonomics |
| Credential model | **One shared Google *Desktop* OAuth client embedded in the package** | Desktop client = public client; secret is non-confidential (PKCE-protected). Precedent: rclone, gcloud CLI ship embedded clients |
| Where tokens live | **On each user's own machine** (`~/.config/google-health-mcp/`) | Claude Code runs locally; no need to host or hold tokens → zero liability |
| OAuth app status | **Production, unverified at launch → pursue verification** | Testing mode expires refresh tokens after 7 days; ship unverified (free, ≤100 users) while the verification review runs in parallel |
| Verification path | **Brand verification + restricted-scope review + CASA** | Required to exceed 100 users / remove the warning; the no-backend design keeps the assessment scope minimal (see §7.2) |
| Distribution | **PyPI package `health-data-connect`**, run via `uvx` / `pipx` | One-line install; matches how `google-health-mcp` is already run |
| Scopes | Inherit `google-health-mcp`'s read-only `googlehealth.*` set for v1 | Least-effort; scope trimming is a future option |

## 4. Architecture

```
                    (Himanshu, one time)
   Google Cloud project ── Desktop OAuth client JSON ──┐
                                                       │ embedded as package data
                                                       ▼
   ┌─────────────────────── health-data-connect (PyPI) ───────────────────────┐
   │  CLI:  auth  |  register  |  disconnect  |  serve                         │
   │  data:  embedded google_client.json (shared, public client)              │
   │  deps:  google-health-mcp                                                 │
   └──────────────┬──────────────────────────────────────────┬────────────────┘
                  │ writes shared client + runs consent       │ delegates
                  ▼                                           ▼
   ~/.config/google-health-mcp/           google_health_mcp.* (tools, API, PKCE auth)
     google_client.json  (from us)                      │
     google_tokens.json  (user's own, local)            ▼
                                             health.googleapis.com/v4  ← user's Fitbit data
```

**Data flow (per user):**
1. `uvx health-data-connect auth` — wrapper writes the embedded `google_client.json` into
   the google-health-mcp config dir (if absent), then invokes `google_health_mcp`'s existing
   Google consent flow (`setup_google_auth`).
2. Browser opens → user selects their Google account → clicks through the "unverified app"
   warning → grants read-only health scopes → local callback exchanges the code (PKCE) →
   tokens saved to `~/.config/google-health-mcp/google_tokens.json` **on the user's machine**.
3. Wrapper prints (or runs) the `claude mcp add` registration line.
4. In Claude Code, the MCP server (`google-health-mcp`, now finding a valid client + token
   file) serves `health_get_sleep`, `health_get_activity`, etc. against the user's data.

## 5. Components

**5.1 Package `health-data-connect`**
- Declares `google-health-mcp` as a dependency (imported, not shelled out to).
- Bundles one package-data file: `google_client.json` (the shared Desktop client), created
  during operator setup (§7).

**5.2 CLI commands**
- `auth` — ensure the embedded client file is present at `google_health_mcp.config.GOOGLE_CLIENT_PATH`
  (write it if missing/stale), then call `google_health_mcp.auth.setup_google_auth()`. On
  success, print the exact registration line pointing at our branded entrypoint:
  `claude mcp add -s user health-data-connect -- uvx health-data-connect serve`.
- `register` (optional convenience) — run that `claude mcp add` command for the user.
- `disconnect` — delete the local `google_tokens.json` and print the
  `myaccount.google.com/permissions` revoke link. (Local wipe + revoke instruction.)
- `serve` (optional) — ensure client file present, then start the underlying
  `google_health_mcp` server. Lets users register `health-data-connect serve` instead of the
  bare `google-health-mcp` if we prefer a single branded entrypoint. **Decision:** ship `serve`
  so onboarding references one tool name throughout.

**5.3 Config seams we rely on (from google-health-mcp, already read):**
- `config.GOOGLE_CLIENT_PATH` = `~/.config/google-health-mcp/google_client.json`
- `config.GOOGLE_TOKENS_PATH` = `~/.config/google-health-mcp/google_tokens.json`
- `config.GOOGLE_HEALTH_MCP_CONFIG_DIR` env override exists if we want isolation.
- `auth.setup_google_auth()` runs the full PKCE consent + token save.
- These are the only integration points; we do not modify upstream code.

## 6. User onboarding flow (the deliverable UX)

Prerequisite: user has `uv` (or `pipx`) installed. One line, then a browser dance:

```
uvx health-data-connect auth
```

The README must hand-hold through the **"Google hasn't verified this app"** screen, because
it is alarming and is the #1 place users bail:
> Click **Advanced** → **Go to health-data-connect (unsafe)** → choose your Google account →
> **Allow**. This warning is expected for a small personal app; you are granting *read-only*
> access to your own health data, and the tokens stay on your machine.

On success the user sees "Tokens saved" and a copy-paste
`claude mcp add -s user health-data-connect -- uvx health-data-connect serve` line (or
`register` does it). Then in Claude Code: *"How did I sleep last week?"* returns real data. Done.

## 7. Operator (Himanshu) one-time setup — reproducible & rotatable

### 7.1 Base setup (launch)
Documented in `docs/operator-setup.md` so the shared client can be recreated or rotated:
1. Create a Google Cloud project; enable the **Health API**.
2. Configure the **OAuth consent screen**: User type **External**; add the read-only
   `googlehealth.*` scopes; fill in app name, logo, support email, and — because we are
   verifying — a **homepage URL** and **privacy-policy URL** from day one (§7.2). Publish to
   **Production** (unverified at launch).
3. Create an **OAuth client of type *Desktop app***; download its JSON.
4. Place the JSON into the package as embedded data (`health_data_connect/google_client.json`).
5. Publish `health-data-connect` to PyPI.

**Rotation:** if the client is abused (quota burn / name impersonation — the only real risks,
neither of which exposes user data), delete the client in Cloud Console, create a new Desktop
client, ship a new package version. *(Note: re-verification may be needed after rotating a
verified client — confirm during the verification process.)*

### 7.2 Verification path (to exceed 100 users / remove the warning)
Restricted `googlehealth.*` scopes require Google's most stringent review. Deliverables:
- **Public homepage** on a domain we own, with **verified domain ownership** in Search Console,
  linked from the consent screen. A single static page is sufficient.
- **Privacy policy** page (same domain) stating exactly what data is accessed, that it is
  read-only, that it stays on the user's device, and that we operate no server.
- **Demo video** (YouTube) showing the OAuth grant and how the data is used, per Google's spec.
- **Scope justification** for each requested scope.
- **CASA security assessment** by a Google-approved assessor. *Open question (§9.5): because we
  have **no backend** and restricted data never transits our servers, the assessment scope should
  be minimal or reduced — confirm the exact tier/requirement with the assessor, since CASA is
  primarily framed around server-side data handling.*

The homepage + privacy policy are small deliverables in this repo (`site/`), deployable as a
static page.

## 8. Security & privacy model

- **Tokens never leave the user's machine.** We have no server and no telemetry.
- **The embedded secret is non-confidential by design** (Desktop/public client + PKCE). Exposure
  is expected, not a leak. Worst-case abuse: app-name impersonation on a consent screen, or
  API-quota burn against our client — fixed by rotation (§7). Neither reaches user data.
- **Read-only scopes only.** No write scopes, no location/GPS scope.
- **Do not log health payloads** anywhere in the wrapper.
- **`disconnect`** gives users a clean off-ramp: local token wipe + Google revoke link.

## 9. Risks & open questions — verify DURING build, before shipping

1. **[LOAD-BEARING] Do unverified-*production* apps get durable refresh tokens?** The 7-day
   refresh-token expiry is confirmed for **Testing** mode; we are *assuming* production-unverified
   is durable. If it is not, the whole one-time-consent UX breaks. → **First build milestone is a
   spike that authorizes, waits >7 days (or otherwise confirms via Google docs/support), and proves
   the token still refreshes.** De-risk this before building anything else.
2. **Does the end user need a Google-migrated Fitbit account?** Unconfirmed by research. Verify
   with a real Fitbit account during the Phase-0 spike.
3. **Exact Fitbit Web API decommission date** (~Sept 30 2026) — confirm on a primary Google page;
   affects urgency messaging only, not architecture.
4. **100-user cap.** Free ceiling for unverified production; we launch here and lift it via
   verification (§7.2) running in parallel.
5. **[VERIFY] Does CASA fully apply to a no-backend on-device app?** The security assessment is
   framed around server-side handling of restricted data; ours never leaves the device. Confirm
   the exact requirement/tier and cost (~$500–$4.5k/yr range) with a Google-approved assessor
   before committing spend. Also confirm whether rotating the embedded client forces re-verification.

## 10. Milestones / build order

0. **De-risk spike** (§9.1 + §9.2): stand up the shared Desktop client, authorize a real Google
   account with a real Fitbit, confirm data flows into Claude Code AND that the refresh token is
   durable. *Gate: if tokens aren't durable in unverified-production, stop and rethink.*
1. **Wrapper package**: `health-data-connect` with embedded client + `auth`/`serve`/`disconnect`/
   `register`, depending on `google-health-mcp`.
2. **Docs**: README with the warning-screen walkthrough; `operator-setup.md`; project `CLAUDE.md`.
3. **Second-machine test**: fresh machine, `uvx health-data-connect auth`, prove the full
   stranger experience end-to-end.
4. **Publish** to PyPI (unverified production; ≤100 users).
5. **Verification track (parallel):** homepage + privacy policy (`site/`), domain ownership,
   demo video, scope justifications, CASA assessment (§7.2). Lifts the cap and warning.

## 11. Out of scope (restating, to prevent scope creep)

Hosted broker · remote MCP · token storage on our side · scope trimming · multi-provider
normalization beyond what `google-health-mcp` already offers · Apple Health / Garmin / Whoop.

*(Verification / >100 users is now IN scope — see §7.2, §10.5.)*
