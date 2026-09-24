"""Google OAuth2 (PKCE) for an installed Desktop client, and token refresh.

A Desktop client is a public client: its "secret" is not confidential, and the
flow is protected by PKCE. Access tokens last an hour; refresh tokens do not
rotate here, so a token minted once keeps working via refresh.
"""

import base64
import hashlib
import html
import json
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import config


class TokenError(RuntimeError):
    """Credentials are missing or the server refused them — re-auth needed."""


def generate_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def load_client() -> dict:
    """Return the `installed` client credentials, or raise TokenError."""
    path = config.GOOGLE_CLIENT_PATH
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise TokenError(
            "No usable OAuth client. Run: health-data-connect auth"
        ) from e
    installed = data.get("installed") if isinstance(data, dict) else None
    if not isinstance(installed, dict) or not installed.get("client_id"):
        raise TokenError("google_client.json is not a Desktop client file.")
    return installed


def _save_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, json.dumps(data, indent=2).encode())
    finally:
        os.close(fd)


def save_tokens(data: dict) -> None:
    _save_json(config.GOOGLE_TOKENS_PATH, data)


def load_tokens() -> dict:
    try:
        data = json.loads(config.GOOGLE_TOKENS_PATH.read_text())
    except (OSError, ValueError) as e:
        raise TokenError("No tokens. Run: health-data-connect auth") from e
    if not isinstance(data, dict):
        raise TokenError("Token file is malformed. Run: health-data-connect auth")
    return data


def _post_form(url: str, fields: dict) -> dict:
    """POST application/x-www-form-urlencoded, return parsed JSON. Seam for tests."""
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise TokenError("Google refused the token request. Run: health-data-connect auth") from e
    except (OSError, ValueError) as e:
        raise TokenError("Could not reach Google to get a token.") from e


def _expires_at(payload: dict) -> float:
    value = payload.get("expires_in", config.GOOGLE_TOKEN_LIFETIME)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        value = config.GOOGLE_TOKEN_LIFETIME
    return time.time() + value


def refresh_token() -> str:
    """Return a valid access token, refreshing via the token endpoint if expired."""
    tokens = load_tokens()
    expires_at = tokens.get("expires_at", 0)
    if not isinstance(expires_at, (int, float)) or isinstance(expires_at, bool):
        expires_at = 0
    if tokens.get("access_token") and time.time() < expires_at - 300:
        return tokens["access_token"]

    if not tokens.get("refresh_token"):
        raise TokenError("No refresh token. Run: health-data-connect auth")

    client = load_client()
    payload = _post_form(
        config.GOOGLE_TOKEN_URL,
        {
            "grant_type": "refresh_token",
            "client_id": client["client_id"],
            "client_secret": client.get("client_secret", ""),
            "refresh_token": tokens["refresh_token"],
        },
    )
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise TokenError("Google returned no access token. Run: health-data-connect auth")

    tokens = {
        "access_token": payload["access_token"],
        "refresh_token": payload.get("refresh_token") or tokens["refresh_token"],
        "expires_at": _expires_at(payload),
    }
    save_tokens(tokens)
    return tokens["access_token"]


def build_auth_url(challenge: str, client_id: str) -> str:
    return config.GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
            "scope": config.GOOGLE_SCOPES,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        }
    )


def exchange_code(code: str, verifier: str, client: dict) -> dict:
    return _post_form(
        config.GOOGLE_TOKEN_URL,
        {
            "client_id": client["client_id"],
            "client_secret": client.get("client_secret", ""),
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": config.GOOGLE_REDIRECT_URI,
        },
    )


def run_setup() -> None:
    """Interactive consent: open a browser, catch the callback, store tokens.

    Raises TokenError / SystemExit-free; the CLI turns failures into exit codes.
    """
    client = load_client()
    verifier, challenge = generate_pkce()
    result: dict = {"code": None, "error": None}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            result["code"] = qs.get("code", [None])[0]
            result["error"] = qs.get("error", [None])[0]
            msg = "Authorised! You can close this tab." if result["code"] else f"Error: {result['error']}"
            body = f"<html><body><h2>{html.escape(msg)}</h2></body></html>".encode()
            self.send_response(200 if result["code"] else 400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):  # the callback URL carries the auth code
            pass

    server = HTTPServer(("localhost", config.GOOGLE_CALLBACK_PORT), Handler)
    url = build_auth_url(challenge, client["client_id"])
    print(f"\nOpening browser for Google authorisation...\nIf it doesn't open, visit:\n{url}\n")
    webbrowser.open(url)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout=180)
    server.server_close()

    if not result["code"]:
        raise TokenError(f"Authorisation failed: {result['error'] or 'no response / timed out'}")

    payload = exchange_code(result["code"], verifier, client)
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise TokenError("Google returned no access token.")
    if not payload.get("refresh_token"):
        raise TokenError(
            "Google returned no refresh token (unattended refresh won't work). "
            "Revoke at myaccount.google.com/permissions and try again."
        )
    save_tokens(
        {
            "access_token": payload["access_token"],
            "refresh_token": payload["refresh_token"],
            "expires_at": _expires_at(payload),
        }
    )
    print("Tokens saved.")
