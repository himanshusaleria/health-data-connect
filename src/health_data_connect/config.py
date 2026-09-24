"""Configuration for the direct Google Health API client.

Paths are overridable via HEALTH_DATA_CONNECT_CONFIG_DIR (used by tests and
multi-config setups). Scopes are read-only and least-privilege: only what the
sleep + activity tools need.
"""

import os
from pathlib import Path

_DEFAULT_CONFIG_DIR = Path.home() / ".config" / "health-data-connect"
CONFIG_DIR = Path(os.environ.get("HEALTH_DATA_CONNECT_CONFIG_DIR", _DEFAULT_CONFIG_DIR))

# The shared public Desktop client we embed, and the user's own tokens.
GOOGLE_CLIENT_PATH = CONFIG_DIR / "google_client.json"
GOOGLE_TOKENS_PATH = CONFIG_DIR / "google_tokens.json"

# Google Health API + OAuth endpoints.
GOOGLE_API_BASE = "https://health.googleapis.com/v4"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Read-only scopes for the first slice (sleep + activity). A scope left out
# costs every user a re-consent, so add here before shipping a tool that needs it.
GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/googlehealth.sleep.readonly "
    "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"
)

# Desktop clients register no redirect URI, so this port is fixed by us.
GOOGLE_CALLBACK_PORT = 8081
GOOGLE_REDIRECT_URI = f"http://localhost:{GOOGLE_CALLBACK_PORT}"

# Access tokens last an hour; used when the token response omits expires_in.
GOOGLE_TOKEN_LIFETIME = 3600
