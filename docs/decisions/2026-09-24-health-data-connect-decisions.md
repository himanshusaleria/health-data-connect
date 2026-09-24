# Decision log — health-data-connect

Chronological record of the non-obvious choices made building this project. Format: **what → choice → why → cost if wrong.**

## 2026-09-23 — Brainstorming & design

- **Build vs. reuse** → *Wrap the existing `google-health-mcp` package, don't build from scratch.* → It already implements every tool + the Google Health API + PKCE auth; only the credential ergonomics were missing. → Cost: coupled to upstream's API/entrypoints.
- **Credential model** → *Embed one shared Google **Desktop** OAuth client in the package.* → A Desktop client is a *public* client; its "secret" is non-confidential (PKCE protects the flow), so one embedded client serves all users and nobody needs their own id/secret. Precedent: rclone, gcloud CLI. → Cost: app-name impersonation / quota burn (mitigated by rotation); never exposes user data.
- **Where tokens live** → *On each user's own machine (`~/.config/google-health-mcp/`).* → Claude Code runs locally, so no server or token storage is needed → zero liability. → Cost: no remote-connector (ChatGPT/Claude.ai-web) support.
- **OAuth app status** → *Publish to Production, unverified at launch; pursue verification in parallel.* → Testing mode expires refresh tokens after 7 days; unverified-production is free up to 100 users. → Cost: users see a one-time "unverified app" warning until verification completes.
- **Audience / scope** → *Public self-serve is the goal; verification (brand + restricted-scope + CASA) is IN scope* (added by user 2026-09-23). → User intends to lift the 100-user cap and remove the warning. → Cost: ~$500–$4.5k/yr + annual assessment; no-backend design keeps assessment scope minimal.
- **Load-bearing risk** → *Gate public launch on confirming unverified-production refresh tokens don't die at 7 days.* → If they do, the one-time-consent UX breaks. → Cost: if unverified prod also 7-day-expires, redesign needed (operator Task 9.3).

## 2026-09-24 — Implementation rulings

- **Python floor** → *`requires-python >= 3.13`* (plan said 3.11). → `google-health-mcp` requires 3.13. → Cost: none, it's the correct floor. `.python-version` pins it for uv.
- **Packaging** → *Dropped the planned `force-include` for the bundled client json.* → Verified hatchling bundles files under the package dir by default (checked via `uv build`). → Cost: none.
- **Isolation** → *Feature branch, not a full git worktree.* → Fresh solo local repo, no remote. → Cost: minimal.
- **Auth exit contract** (from code review) → *`_cmd_auth` catches `SystemExit`, not just `TokenRefused`.* → Upstream signals consent denial/timeout via `sys.exit(1)`, not an exception; the wrapper now owns its non-zero return and the test models the real path. → Cost: none.
- **Integration** → *Merged to `main` locally and pushed to a new **private** GitHub repo* (`himanshusaleria/health-data-connect`) per user request. → Solo project, review complete. → Cost: none.

## Open operator gates (not code — Himanshu)

1. Create Google Cloud project + Health API + Desktop OAuth client; embed real client_id/secret (replace placeholders). See `docs/operator-setup.md`.
2. Confirm the 7-day refresh-token durability gate before public launch.
3. Publish to PyPI (`RELEASE=1` release guard must pass).
4. Verification track: homepage + privacy policy (`site/`), domain ownership, demo video, scope justifications, CASA.

## 2026-09-24 (later) — Architecture pivot: build direct on Google APIs

- **Drop the wrap/fork of `google-health-mcp`** → *Build directly on the Google Health API instead.* → The dependency's hard `>=3.13` floor broke `pip install` on the user's machine (conda base 3.12); depending on a third party's arbitrary constraints + semi-internal imports is too fragile for a public, verified product. → Cost: we re-implement the OAuth + endpoint layer ourselves (but we control the Python floor, scopes, and audit surface).
- **Incremental scope** → *Ship a couple of endpoints first (recommend sleep + activity), expand later.* → Don't wrap all ~17 data types up front; prove value, then grow. → Cost: fewer metrics at launch.
- **Credential model unchanged** → embedded public Desktop client + on-device tokens still stands (independent of wrap-vs-direct).
- **Python floor** → *own build targets 3.11+* → removes the 3.13 install pain that killed the wrapper path.
- **CLI for coding agents** → *parked as a later todo* (per user).
- **Product framing** → *"like the tool the user installed (google-health-mcp), but marketed well + multi-device."* → Differentiator is go-to-market + multi-provider, not the raw API access.
- **Superseded:** `src/health_data_connect/` (the wrapper + `ensure_client` around google-health-mcp) will be replaced by a direct-API implementation; kept in git history.

