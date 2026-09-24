"""health-data-connect CLI: auth | serve | disconnect | register."""

import argparse
import sys
from pathlib import Path

from google_health_mcp import config
from google_health_mcp.auth import TokenRefused, setup_google_auth

from .client import ensure_client

REGISTER_CMD = "claude mcp add -s user health-data-connect -- uvx health-data-connect serve"
REVOKE_URL = "https://myaccount.google.com/permissions"


def _cmd_auth() -> int:
    ensure_client()
    try:
        setup_google_auth()
    except TokenRefused as e:
        print(e, file=sys.stderr)
        return 1
    print("\nConnected. Register with your MCP client:\n  " + REGISTER_CMD)
    return 0


def run_server() -> None:
    # Importing the upstream cli registers every tool on its shared `mcp` instance.
    from google_health_mcp.cli import mcp

    mcp.run(transport="stdio")


def _cmd_serve() -> int:
    ensure_client()
    run_server()
    return 0


def _cmd_disconnect() -> int:
    tokens = Path(config.GOOGLE_TOKENS_PATH)
    tokens.unlink(missing_ok=True)
    print(f"Local tokens removed. Also revoke access at: {REVOKE_URL}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="health-data-connect")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    sub.add_parser("auth", help="Connect your Google/Fitbit account (browser consent)")
    sub.add_parser("serve", help="Run the MCP server (stdio)")
    sub.add_parser("disconnect", help="Delete local tokens and show the revoke link")
    args = parser.parse_args(argv)
    if args.cmd == "auth":
        return _cmd_auth()
    if args.cmd == "serve":
        return _cmd_serve()
    if args.cmd == "disconnect":
        return _cmd_disconnect()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
