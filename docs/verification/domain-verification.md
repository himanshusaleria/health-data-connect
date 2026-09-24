# Domain / site verification for OAuth

The site is live via GitHub Pages: **https://himanshusaleria.github.io/health-data-connect/**
- Homepage: `/` · Privacy: `/privacy.html` · Terms: `/terms.html`
- Source: the `gh-pages` branch (files at root, `.nojekyll`). To update, edit `site/*.html` on
  `main`, then copy them onto `gh-pages` and push (or we automate later).

## What each launch stage needs

### Now — unverified production (≤100 users)
**No domain verification required.** The consent screen only needs working homepage + privacy
URLs, which we now have. Put these in the OAuth consent screen:
- Application home page: `https://himanshusaleria.github.io/health-data-connect/`
- Privacy policy: `https://himanshusaleria.github.io/health-data-connect/privacy.html`
- Terms of service: `https://himanshusaleria.github.io/health-data-connect/terms.html`

### Later — full verification (public / CASA)
Google's brand verification wants an **authorized domain you own and have verified** in Search
Console. `github.io` is owned by GitHub, not you, so for *full* verification you will likely need
a **custom domain**:
1. Buy a domain (Track C), e.g. `healthdataconnect.app`.
2. Point it at GitHub Pages (add a `CNAME` file to `gh-pages` + DNS records), or host `site/`
   elsewhere.
3. Verify it in **Google Search Console** (DNS TXT record is easiest for a domain-level property).
4. Add it as an **Authorized domain** on the OAuth consent screen; update the three URLs above.

### Verifying the github.io site now (optional, for a URL-prefix property)
If you want it verified before a custom domain: in Search Console add a **URL-prefix** property for
`https://himanshusaleria.github.io/health-data-connect/`, choose **HTML file** verification, and
drop the `google<...>.html` file Google gives you onto the `gh-pages` branch root. (Meta-tag
verification also works — add it to `index.html`.)

## Note
Keep the homepage/privacy/terms URLs identical everywhere (consent screen, scope justifications,
demo video) — reviewers cross-check them.
