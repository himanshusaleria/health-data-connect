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
4. Save the downloaded JSON somewhere safe and private, e.g. `~/.config/health-data-connect/google_client.json`.
   The repo keeps the **placeholder** in `src/health_data_connect/data/google_client.json` — the real
   client is **injected at release time and never committed** (GitHub push protection blocks it, and
   it keeps the secret out of git history). A Desktop client's secret is a *public* client secret and
   ships in the PyPI wheel regardless, so this is about hygiene, not confidentiality.
5. Authorize one real Google account that has real Fitbit data (this is also how you use the app).

## 1a. Releasing to PyPI

The published wheel must contain the real client; the git repo must not. Steps:
```bash
cp ~/.config/health-data-connect/google_client.json src/health_data_connect/data/google_client.json  # inject
RELEASE=1 uv run pytest                 # release guard: fails on placeholder creds
uv build                                # build wheel + sdist from the injected working tree
uv publish --token "$(cat .pypi.token)" # .pypi.token is gitignored
git checkout -- src/health_data_connect/data/google_client.json  # restore placeholder; do NOT commit the real client
git tag -a vX.Y.Z -m "..." && git push origin main --tags
```
Bump `version` in `pyproject.toml` first — a PyPI version can never be re-uploaded.

## 2. Rotation

If the client is abused (API-quota burn or app-name impersonation on a consent screen — neither
exposes any user's data): delete the client in Cloud Console, create a new **Desktop app** client,
save it to `~/.config/health-data-connect/google_client.json`, and ship a new version via the
release steps above. (A verified client may need re-verification after rotation — confirm during it.)

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
