# Launch checklist — everything *besides* building

Goal: make health-data-connect available to the general public — a well-marketed, multi-device
"talk to your wearable data in your AI assistant" tool. This lists the **non-code** work.

Legend: **[You]** = needs Himanshu (account/payment/decision/voice) · **[Me]** = I can draft/do ·
**[Both]** = I draft, you approve/act. Ordered roughly by dependency.

---

## Track A — Google OAuth verification (the gate for public scale)
Restricted health scopes → no getting around this for >100 users / removing the warning.
- [ ] **[You]** Create Google Cloud project; enable the Health API.
- [ ] **[You]** Create a **Desktop** OAuth client; embed real client_id/secret in the package.
- [ ] **[You]** OAuth consent screen: External, restricted scopes, app name + logo + support email + homepage + privacy URL.
- [ ] **[You]** Verify **domain ownership** in Google Search Console (needs the domain from Track C).
- [ ] **[Me]** Draft **scope justifications** (one per `googlehealth.*` scope).
- [ ] **[Both]** **Demo video** for review — I script, you record.
- [ ] **[You]** Engage a Google-approved **CASA** assessor; **confirm whether a no-backend on-device app needs the full assessment** (may be minimal). Budget ~$500–$4.5k/yr.
- [ ] **[You]** **Durability gate:** confirm unverified-production refresh tokens don't expire at 7 days *before* public launch.

## Track B — Legal & compliance
- [ ] **[Me]** Finalize **privacy policy** to Google's restricted-scope wording (draft in `site/`).
- [ ] **[Me]** **Terms of Service** + health disclaimer ("not medical advice").
- [ ] **[Me]** Data-handling statement (on-device only, no server, no collection) — consistent everywhere.
- [ ] **[Both]** GDPR/CCPA posture — minimal since we collect nothing, but state it explicitly.
- [ ] **[You]** Decide the **legal contact / entity** named on the consent screen & policies.

## Track C — Domain, hosting, brand
- [ ] **[You]** Decide the **public product name** ("health-data-connect" is a placeholder — pick something brandable).
- [ ] **[You]** Register a **domain**.
- [ ] **[Me]** Deploy homepage + privacy + terms (`site/`) to Vercel/GitHub Pages.
- [ ] **[Both]** **Logo / consent-screen icon**.

## Track D — Distribution
- [ ] **[Both]** Publish to **PyPI** (after client embedded + release guard passes).
- [ ] **[Me]** Set a friendly **Python floor (3.11)** so `pip`/`uvx` work broadly (fixes the 3.13 pain).
- [ ] **[Me]** List in **MCP registries** (official MCP registry, Smithery, Claude connector directory).
- [ ] **[Me]** Polish install docs / README / quickstart GIF.

## Track E — Marketing / go-to-market
- [ ] **[Both]** Positioning & messaging (your voice; I draft options).
- [ ] **[Me→You send]** Launch posts (draft only — you post): **Show HN**, Reddit (r/QuantifiedSelf, r/Fitbit, r/ClaudeAI, r/mcp, r/oura, r/whoop), X, **Product Hunt**, MCP/Claude communities.
- [ ] **[Me]** Landing-page copy + a demo GIF/video.
- [ ] **[Me]** SEO/GEO content (blog, comparison pages, "connect Fitbit to Claude/ChatGPT" keywords).
- [ ] **[You]** Launch timing / coordination.

## Track F — Support & ops
- [ ] **[You]** Support email (ashish@qaby.ai works) + enable GitHub Issues when public.
- [ ] **[Me]** FAQ / troubleshooting — esp. the "unverified app" screen and Fitbit→Google account migration.
- [ ] **[You]** Decide on **privacy-respecting analytics/feedback** (likely none, or opt-in only).
- [ ] **[Me]** OAuth-client **rotation / incident** runbook.

## Track G — Open decisions (blocking several tracks)
- [ ] **[You]** **Open source or private?** (recommendation: open source / MIT — transparency aids a privacy tool + verification.)
- [ ] **[You]** **Monetization:** free / donations / paid tiers? (affects legal + positioning.)
- [ ] **[You]** **First 2 APIs** to ship (recommendation: **sleep + activity** — highest interest, simplest).

## Track H — Roadmap (later — parked todos)
- [ ] **CLI for coding agents** (deferred per your note).
- [ ] **Multi-device provider adapters:** Google Health (Fitbit/Pixel) → Oura → Whoop → Google Fit / Android Health Connect → Apple Health & Garmin (both have constraints we researched).
- [ ] **Normalization layer** — same schema across providers.
