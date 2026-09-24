# Operator setup (Himanshu)

How to create/rotate the shared Google OAuth client that `health-data-connect` embeds, and how
to pursue app verification. Users never do any of this — they just run `uvx health-data-connect
auth`.

## 1. Base setup (launch)

1. Create a **Google Cloud project**; enable the **Health API**.
2. Configure the **OAuth consent screen**:
   - User type: **External**.
   - Add the read-only scopes the app uses (first slice): `googlehealth.sleep.readonly` and
     `googlehealth.activity_and_fitness.readonly`. Both are *restricted* scopes. (Add more here
     as we ship more metrics — a scope left out costs every user a re-consent.)
   - Fill app name, logo, support email, **homepage URL**, and **privacy-policy URL** (deploy
     `site/index.html` and `site/privacy.html`). Set these from day one — verification needs them.
   - Publish to **Production** (leave it unverified for now).
3. Create credentials → **OAuth client ID** → application type **Desktop app**. Download the JSON.
4. Open `src/health_data_connect/data/google_client.json` and replace the two placeholder values
   with the real ones from the downloaded JSON:
   - `REPLACE_WITH_REAL_CLIENT_ID.apps.googleusercontent.com` → your real `client_id`
   - `REPLACE_WITH_REAL_CLIENT_SECRET` → your real `client_secret`
   (A Desktop client's secret is a *public* client secret — safe to embed. PKCE protects the flow.)
5. Authorize one real Google account that has real Fitbit data and **record the date** — you'll
   use it to confirm the refresh token is still valid after 7 days (see the durability gate in the
   implementation plan, Task 9).
6. Publish to PyPI (see the plan's Task 9 — the release guard blocks a build with placeholders).

## 2. Rotation

If the client is abused (API-quota burn or app-name impersonation on a consent screen — neither
exposes any user's data): delete the client in Cloud Console, create a new **Desktop app** client,
swap its values into `src/health_data_connect/data/google_client.json`, and ship a new version.
(A verified client may need re-verification after rotation — confirm during the process.)

## 3. Verification (to exceed 100 users / remove the warning)

Restricted `googlehealth.*` scopes require Google's most stringent review. Deliverables:

- **Public homepage** on a domain you own, with **verified domain ownership** in Search Console,
  linked from the consent screen. (`site/index.html`.)
- **Privacy policy** on the same domain stating: exactly what data is accessed, that it is
  read-only, that it stays on the user's device, and that we operate no server. (`site/privacy.html`.)
- **Demo video** (YouTube) showing the OAuth grant and how the data is used.
- **Scope justification** for each requested scope.
- **CASA security assessment** by a Google-approved assessor.
  - *Open question:* because there is **no backend** and restricted data never transits our
    servers, the assessment scope should be minimal — CASA is framed around server-side data
    handling. Confirm the exact tier, requirement, and cost (~$500–$4,500/yr range) with the
    assessor before committing spend.
