import base64
import hashlib
import json
import time

from health_data_connect import auth


def test_pkce_challenge_matches_verifier():
    verifier, challenge = auth.generate_pkce()
    assert 43 <= len(verifier) <= 128
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    assert challenge == expected


def test_load_client_reads_installed(tmp_path, monkeypatch):
    path = tmp_path / "google_client.json"
    path.write_text('{"installed": {"client_id": "abc", "client_secret": "s"}}')
    monkeypatch.setattr(auth.config, "GOOGLE_CLIENT_PATH", path)
    client = auth.load_client()
    assert client["client_id"] == "abc"


def test_load_client_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(auth.config, "GOOGLE_CLIENT_PATH", tmp_path / "nope.json")
    try:
        auth.load_client()
        assert False, "expected TokenError"
    except auth.TokenError:
        pass


def test_build_auth_url_has_pkce_and_offline():
    url = auth.build_auth_url("CHAL", "CID")
    assert "code_challenge=CHAL" in url
    assert "code_challenge_method=S256" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "client_id=CID" in url


def test_refresh_returns_cached_when_valid(tmp_path, monkeypatch):
    tokens = tmp_path / "google_tokens.json"
    tokens.write_text(json.dumps({"access_token": "CACHED", "refresh_token": "r", "expires_at": time.time() + 3600}))
    monkeypatch.setattr(auth.config, "GOOGLE_TOKENS_PATH", tokens)

    def explode(*a, **k):
        raise AssertionError("must not hit the network when the token is valid")

    monkeypatch.setattr(auth, "_post_form", explode)
    assert auth.refresh_token() == "CACHED"


def test_refresh_calls_endpoint_when_expired(tmp_path, monkeypatch):
    tokens = tmp_path / "google_tokens.json"
    tokens.write_text(json.dumps({"access_token": "OLD", "refresh_token": "r", "expires_at": 0}))
    client = tmp_path / "google_client.json"
    client.write_text('{"installed": {"client_id": "cid", "client_secret": "sec"}}')
    monkeypatch.setattr(auth.config, "GOOGLE_TOKENS_PATH", tokens)
    monkeypatch.setattr(auth.config, "GOOGLE_CLIENT_PATH", client)
    monkeypatch.setattr(auth, "_post_form", lambda url, fields: {"access_token": "NEW", "expires_in": 3600})

    assert auth.refresh_token() == "NEW"
    saved = json.loads(tokens.read_text())
    assert saved["access_token"] == "NEW"
    assert saved["refresh_token"] == "r"  # carried forward when the response omits it
