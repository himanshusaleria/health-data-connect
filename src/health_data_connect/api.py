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
from datetime import date, timedelta

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


def _post_json(url: str, headers: dict, body: dict) -> dict:
    """POST a JSON body and parse the JSON response. Seam for tests."""
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers, method="POST"
    )
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
        parsed = json.loads(raw)
    except ValueError as e:
        raise ApiError("Google returned an unreadable response.") from e
    if not isinstance(parsed, dict):
        raise ApiError("Google returned an unexpected response shape.")
    return parsed


def google_post(path: str, body: dict) -> dict:
    """One authenticated POST against the Health API."""
    token = refresh_token()
    url = f"{config.GOOGLE_API_BASE}/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    return _post_json(url, headers, body)


def _civil(day: date) -> dict:
    return {"date": {"year": day.year, "month": day.month, "day": day.day}}


def daily_roll_up(type_path: str, start: date, end: date, cap_days: int = 90) -> list[dict]:
    """One point per day for a type over [start, end), in cap-sized chunks.

    Google caps a single dailyRollUp window (14 days for the calorie family, 90
    otherwise), so we chunk. Response points arrive under `rollupDataPoints`.
    """
    if start >= end:
        return []
    points: list[dict] = []
    window_start = start
    while window_start < end:
        window_end = min(window_start + timedelta(days=cap_days), end)
        body = google_post(
            f"users/me/dataTypes/{type_path}/dataPoints:dailyRollUp",
            {"range": {"start": _civil(window_start), "end": _civil(window_end)}, "windowSizeDays": 1},
        )
        page = body.get("rollupDataPoints")
        if page is not None and not isinstance(page, list):
            raise ApiError("Google returned an unexpected response shape.")
        points.extend(page or [])
        window_start = window_end
    return points


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
