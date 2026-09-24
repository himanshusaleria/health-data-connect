"""Authenticated Google Health API client with paging.

Endpoints (v4):
  GET  {base}/users/me/dataTypes/{type}/dataPoints?filter=...&pageSize=...&pageToken=...
An empty page carrying a nextPageToken is NOT the end of data — only an absent
or empty token ends the walk.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

from . import config
from .auth import TokenError, refresh_token

MAX_PAGES = 500
DEFAULT_PAGE_SIZE = 10000
SESSION_PAGE_SIZE = 25  # sleep and exercise cap here


class ApiError(RuntimeError):
    """A Google Health API request failed."""


def _get_json(url: str, headers: dict) -> dict:
    """GET a URL and parse JSON. Seam for tests."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise TokenError(
                "Google refused the request (token or scope). Run: health-data-connect auth"
            ) from e
        raise ApiError(f"API error {e.code}") from e
    except (OSError, ValueError) as e:
        raise ApiError("Network error reaching the Google Health API.") from e
    try:
        body = json.loads(raw)
    except ValueError as e:
        raise ApiError("Google returned an unreadable response.") from e
    if not isinstance(body, dict):
        raise ApiError("Google returned an unexpected response shape.")
    return body


def google_get(path: str, params: dict) -> dict:
    """One authenticated GET against the Health API."""
    token = refresh_token()
    url = f"{config.GOOGLE_API_BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    return _get_json(url, headers)


def build_filter(field: str, start: date, end: date) -> str:
    """Half-open range filter [start, end) in the date literal the API expects."""
    return f'{field} >= "{start.isoformat()}" AND {field} < "{end.isoformat()}"'


def list_data_points(
    type_path: str, filter_field: str, start: date, end: date, page_size: int = DEFAULT_PAGE_SIZE
) -> list[dict]:
    """Every data point of one type in [start, end), following pages to exhaustion."""
    if start >= end:
        return []
    points: list[dict] = []
    token = None
    for _ in range(MAX_PAGES):
        params = {"filter": build_filter(filter_field, start, end), "pageSize": page_size}
        if token:
            params["pageToken"] = token
        body = google_get(f"users/me/dataTypes/{type_path}/dataPoints", params)
        page = body.get("dataPoints")
        if page is not None and not isinstance(page, list):
            raise ApiError("Google returned an unexpected response shape.")
        points.extend(page or [])
        token = body.get("nextPageToken")
        if not token:
            return points
    raise ApiError(f"too many pages for {type_path}")
