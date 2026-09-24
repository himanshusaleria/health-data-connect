# CASA scoping — email draft (DO NOT SEND until you decide to pursue verification)

CASA (Cloud Application Security Assessment) is required to publish a **verified** app using
restricted Google health scopes for **>100 users**. Before committing spend, confirm the scope —
our app has **no backend**, which should minimize (or possibly waive) the assessment.

**Who to contact:** a Google-approved CASA assessor (Google lists them; e.g. TAC Security,
Bishop Fox, NCC Group, Leviathan). Get quotes from 2–3.

**Before sending:** fill in the product name/domain if changed, and confirm you actually want to
proceed to public scale. You send this — I only draft.

---

**Subject:** CASA scoping for a no-backend, on-device app (Google restricted health scopes)

Hi <assessor>,

I'm preparing a Google OAuth verification for a small open-source app, **health-data-connect**
(https://himanshusaleria.github.io/health-data-connect/), and would like a scoping call + quote
for the required CASA assessment.

Key architecture details, since they affect assessment scope:
- It's an **installed desktop application** (a local MCP server) that runs entirely on the
  end user's own machine. There is **no backend server** and **no cloud infrastructure** we operate.
- It reads the user's own Google Health data **read-only** (scopes:
  `googlehealth.sleep.readonly`, `googlehealth.activity_and_fitness.readonly`).
- User OAuth tokens and health data are stored and processed **only on the user's device**; we
  never receive, store, or transmit them. We have no database, no API, no servers.
- The code is **open source** (MIT).

Given there is no server-side handling of restricted data, could you advise:
1. Which CASA tier/assessment level applies (and whether a self-assessment/DAST tier is sufficient)?
2. Estimated cost and timeline?
3. What artifacts you'd need from us (repo access, architecture doc, data-flow diagram)?

Happy to hop on a short call. Thanks,
Himanshu
