# OAuth verification — demo video script

Google's restricted-scope review requires a video that shows: the OAuth consent screen with
**your** client (the client_id/project must match the one under review), the exact scopes being
granted, and how the granted data is used. Keep it 2–4 minutes, screen-recorded, narrated.

**Prereq:** the real embedded client must be in place (operator setup) so the consent screen
shows the app under review — not the placeholder.

---

## Shot list

1. **Intro (15s).** On the homepage (<DOMAIN>): "This is health-data-connect, a local,
   open-source tool that lets you ask your own AI assistant about your Fitbit / Google Health
   data. It runs entirely on your machine and stores nothing on any server."

2. **Show the OAuth client identity (10s).** Briefly show the Google Cloud console OAuth client
   page (project name + client_id) so the reviewer can confirm the video matches the app under
   review. (Blur nothing that identifies the client; do not show the client secret.)

3. **Start the flow (15s).** In a terminal: `uvx health-data-connect auth`. Narrate: "One
   command. It opens Google's consent screen in my browser."

4. **Consent screen (30s).** Show the account chooser, then the consent screen. Read the
   requested scopes aloud: "It's asking for **read-only** access to my **sleep** and my
   **activity and fitness** data — nothing else, and nothing write." Click **Allow**.
   (If the app is still unverified when recording, briefly show the "unverified app" →
   Advanced → Continue path and note it disappears after verification.)

5. **Where the data goes (20s).** Show the terminal "Tokens saved" and the local file at
   `~/.config/health-data-connect/google_tokens.json` (do not show its contents). Narrate:
   "The token is stored only here, on my device. No server of ours ever sees it."

6. **Using the data (45s).** In Claude Code, ask: "How did I sleep last week?" and "How active
   was I this month?" Show the assistant calling `get_sleep` / `get_activity` and answering from
   real data. Narrate: "The data is read on my device and used only to answer my own question."

7. **Revoke (20s).** Run `uvx health-data-connect disconnect`; show the revoke link. Narrate:
   "I can delete the local token and revoke access at myaccount.google.com/permissions anytime."

8. **Close (10s).** "Read-only. On-device. No server. Open source." Show the GitHub URL.

## Narration checklist (Google looks for these)
- [ ] Scopes named explicitly and shown on the consent screen
- [ ] Read-only stated
- [ ] Where data is stored / that no server receives it
- [ ] How the data is used (answer the user's own questions locally)
- [ ] How to revoke
