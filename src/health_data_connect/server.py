"""MCP server exposing the health tools over stdio.

Logging goes to stderr; stdout is reserved for JSON-RPC.
"""

import json
import logging
import sys

from mcp.server.fastmcp import FastMCP

from . import health
from .api import ApiError
from .auth import TokenError

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s", stream=sys.stderr)

mcp = FastMCP("health-data-connect")


def sleep_report(start_date=None, end_date=None) -> str:
    try:
        entries = health.get_sleep(start_date, end_date)
    except (TokenError, ApiError) as e:
        return json.dumps({"error": str(e)})
    if not entries:
        return json.dumps({"message": "No sleep data for this period.",
                           "hint": "Check the date range or that your device has synced."})
    return json.dumps({"sleep": entries, "count": len(entries)})


def activity_report(start_date=None, end_date=None) -> str:
    try:
        entries = health.get_activity(start_date, end_date)
    except (TokenError, ApiError) as e:
        return json.dumps({"error": str(e)})
    if not entries:
        return json.dumps({"message": "No activity data for this period.",
                           "hint": "Check the date range or that your device has synced."})
    return json.dumps({"activity": entries, "count": len(entries)})


@mcp.tool()
def get_sleep(start_date: str | None = None, end_date: str | None = None) -> str:
    """Get nightly sleep (duration + stage breakdown).

    Args:
        start_date: "YYYY-MM-DD". Default: 30 days ago.
        end_date: "YYYY-MM-DD". Default: today.

    Returns one entry per night with total_minutes and deep/light/REM/wake minutes.
    """
    return sleep_report(start_date, end_date)


@mcp.tool()
def get_activity(start_date: str | None = None, end_date: str | None = None) -> str:
    """Get daily activity (steps, distance km, floors, calories out).

    Args:
        start_date: "YYYY-MM-DD". Default: 30 days ago.
        end_date: "YYYY-MM-DD". Default: today.

    Returns one entry per day.
    """
    return activity_report(start_date, end_date)


def run_server() -> None:
    mcp.run(transport="stdio")
