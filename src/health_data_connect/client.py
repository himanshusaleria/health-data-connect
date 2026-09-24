"""Place our shared, public Desktop OAuth client where google-health-mcp reads it."""

import os
from importlib.resources import files
from pathlib import Path

from google_health_mcp import config


def _bundled_client_bytes() -> bytes:
    return files("health_data_connect").joinpath("data/google_client.json").read_bytes()


def ensure_client() -> Path:
    target = Path(config.GOOGLE_CLIENT_PATH)
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, _bundled_client_bytes())
    finally:
        os.close(fd)
    return target
