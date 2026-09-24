"""health-data-connect CLI: auth | serve | disconnect | register."""

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from . import config
from .auth import TokenError, run_setup
from .client import ensure_client
from .server import run_server

REGISTER_CMD = "claude mcp add -s user health-data-connect -- uvx health-data-connect serve"
REVOKE_URL = "https://myaccount.google.com/permissions"


def _cmd_auth() -> int:
    ensure_client()
    try:
        run_setup()
    except TokenError as e:
        print(e, file=sys.stderr)
        return 1
    print("\nConnected. Register with your MCP client:\n  " + REGISTER_CMD)
    return 0


def _cmd_serve() -> int:
    ensure_client()
    run_server()
    return 0


def _cmd_disconnect() -> int:
    Path(config.GOOGLE_TOKENS_PATH).unlink(missing_ok=True)
    print(f"Local tokens removed. Also revoke access at: {REVOKE_URL}")
    return 0


def _cmd_register() -> int:
    try:
        subprocess.run(shlex.split(REGISTER_CMD))
    except FileNotFoundError:
        print("`claude` not found. Register manually with:\n  " + REGISTER_CMD)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="health-data-connect")
    sub = parser.add_subparsers(dest="cmd", metavar="COMMAND")
    sub.add_parser("auth", help="Connect your Google/Fitbit account (browser consent)")
    sub.add_parser("serve", help="Run the MCP server (stdio)")
    sub.add_parser("disconnect", help="Delete local tokens and show the revoke link")
    sub.add_parser("register", help="Register this server with Claude Code")
    args = parser.parse_args(argv)
    dispatch = {
        "auth": _cmd_auth,
        "serve": _cmd_serve,
        "disconnect": _cmd_disconnect,
        "register": _cmd_register,
    }
    handler = dispatch.get(args.cmd)
    if handler is None:
        parser.print_help()
        return 1
    return handler()


if __name__ == "__main__":
    sys.exit(main())
