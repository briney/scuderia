#!/usr/bin/env python3
"""
Granola MCP bridge — call Granola MCP tools from the terminal.

This script exists because glm-5.2 (and possibly other models) cannot emit
native MCP tool calls (mcp__granola__*) — the model generates prose and stops
without ever emitting the function-call XML. This script wraps all Granola MCP
calls behind a CLI so the agent can use them via `terminal`.

Usage:
    python3 granola_mcp.py account_info
    python3 granola_mcp.py list_meetings [--range last_week|last_30_days|this_week]
    python3 granola_mcp.py get_meetings MEETING_ID [MEETING_ID ...]
    python3 granola_mcp.py get_transcript MEETING_ID
    python3 granola_mcp.py query "natural language query"

OAuth tokens are read from the profile's mcp-tokens directory. The token is
refreshed automatically by the MCP client if it has a refresh_token.

Exit codes:
    0 — success
    1 — MCP/OAuth error
    2 — no meetings found / empty result (not an error)
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# --- Configuration --------------------------------------------------------

PROFILE_DIR = Path(os.environ.get(
    "HERMES_HOME", os.environ.get("PROFILE_DIR", os.path.expanduser(
        "~/.hermes/profiles/atticus"
    ))
))
TOKEN_PATH = PROFILE_DIR / "mcp-tokens" / "granola.json"
GRANOLA_URL = "https://mcp.granola.ai/mcp"

# --- MCP client -----------------------------------------------------------


async def _get_session():
    """Connect to Granola MCP and return an active ClientSession."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    if not TOKEN_PATH.exists():
        print(json.dumps({
            "error": f"OAuth token file not found: {TOKEN_PATH}",
            "hint": "Run `hermes mcp login granola` in a terminal to authenticate.",
        }), file=sys.stderr)
        sys.exit(1)

    with open(TOKEN_PATH) as f:
        token_data = json.load(f)

    access_token = token_data.get("access_token")
    if not access_token:
        print(json.dumps({
            "error": "No access_token in token file",
            "hint": "Run `hermes mcp login granola` to re-authenticate.",
        }), file=sys.stderr)
        sys.exit(1)

    # Check expiry
    expires_at = token_data.get("expires_at", 0)
    if expires_at and time.time() > expires_at:
        # The MCP client should auto-refresh using the refresh_token,
        # but warn in case it fails
        print(json.dumps({
            "warning": "Access token has expired; attempting refresh...",
        }), file=sys.stderr)

    headers = {"Authorization": f"Bearer {access_token}"}

    transport = streamablehttp_client(GRANOLA_URL, headers=headers)
    read_stream, write_stream, _ = await transport.__aenter__()
    session = ClientSession(read_stream, write_stream)
    await session.__aenter__()
    return session, transport


async def _close(session, transport):
    await session.__aexit__(None, None, None)
    await transport.__aexit__(None, None, None)


async def _call_tool(tool_name, arguments):
    """Call a Granola MCP tool and return its text output."""
    session, transport = await _get_session()
    try:
        result = await session.call_tool(tool_name, arguments)
        texts = []
        for content in result.content:
            if hasattr(content, "text"):
                texts.append(content.text)
        return "\n".join(texts)
    finally:
        await _close(session, transport)


# --- CLI commands ---------------------------------------------------------


async def cmd_account_info(args):
    out = await _call_tool("get_account_info", {})
    print(out)


async def cmd_list_meetings(args):
    kwargs = {}
    if args.range:
        kwargs["time_range"] = args.range
    if args.range == "custom":
        if not args.start:
            print(json.dumps({"error": "--start is required when --range=custom"}), file=sys.stderr)
            sys.exit(1)
        kwargs["custom_start"] = args.start
        if args.end:
            kwargs["custom_end"] = args.end
    out = await _call_tool("list_meetings", kwargs)
    print(out)


async def cmd_get_meetings(args):
    out = await _call_tool("get_meetings", {"meeting_ids": args.meeting_ids})
    print(out)


async def cmd_get_transcript(args):
    out = await _call_tool("get_meeting_transcript", {"meeting_id": args.meeting_id})
    print(out)


async def cmd_query(args):
    out = await _call_tool("query_granola_meetings", {"query": args.query})
    print(out)


# --- Main -----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Granola MCP bridge — call Granola MCP tools from the terminal"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("account_info", help="Get Granola account info")

    p_list = sub.add_parser("list_meetings", help="List recent meetings")
    p_list.add_argument(
        "--range", choices=["this_week", "last_week", "last_30_days", "custom"],
        default=None, help="Time range (default: last_30_days)"
    )
    p_list.add_argument(
        "--start", default=None,
        help="Custom range start (ISO date YYYY-MM-DD, required if --range=custom)"
    )
    p_list.add_argument(
        "--end", default=None,
        help="Custom range end (ISO date YYYY-MM-DD, required if --range=custom)"
    )

    p_get = sub.add_parser("get_meetings", help="Get meeting details by ID")
    p_get.add_argument("meeting_ids", nargs="+", help="Meeting UUID(s)")

    p_transcript = sub.add_parser("get_transcript", help="Get meeting transcript")
    p_transcript.add_argument("meeting_id", help="Meeting UUID")

    p_query = sub.add_parser("query", help="Query meetings in natural language")
    p_query.add_argument("query", help="Natural language query")

    args = parser.parse_args()

    cmd_map = {
        "account_info": cmd_account_info,
        "list_meetings": cmd_list_meetings,
        "get_meetings": cmd_get_meetings,
        "get_transcript": cmd_get_transcript,
        "query": cmd_query,
    }

    try:
        asyncio.run(cmd_map[args.command](args))
    except Exception as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
