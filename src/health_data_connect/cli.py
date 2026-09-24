"""health-data-connect CLI: auth | serve | disconnect | register."""

import argparse
import sys

from google_health_mcp.auth import TokenRefused, setup_google_auth

from .client import ensure_client

REGISTER_CMD = "claude mcp add -s user health-data-connect -- uvx health-data-connect serve"


def _cmd_auth() -> int:
    ensure_client()
    try:
        setup_google_auth()
    except TokenRefused as e:
        print(e, file=sys.stderr)
        return 1
    print("\nConnected. Register with your MCP client:\n  " + REGISTER_CMD)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="health-data-connect")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    sub.add_parser("auth", help="Connect your Google/Fitbit account (browser consent)")
    args = parser.parse_args(argv)
    if args.cmd == "auth":
        return _cmd_auth()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
