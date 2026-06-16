#!/usr/bin/env python3
"""Example: call the MCP server's tools in-process.

Usage:
    pip install "acmt001[servers]"     # requires Python 3.10+
    python examples/mcp_tools.py

The acmt001 MCP server (launched as `acmt001-mcp` over stdio) exposes the
library to AI agents. This example invokes the same tools directly through the
FastMCP instance, without a transport, to show what an agent would receive.
"""

import asyncio
import json
from pathlib import Path

try:
    from acmt001.mcp.server import server
except ModuleNotFoundError:
    raise SystemExit(
        "The MCP server requires the optional 'servers' extra:\n"
        '    pip install "acmt001[servers]"   (Python 3.10+)'
    ) from None

record = json.loads(
    (
        Path(__file__).resolve().parent.parent
        / "tests"
        / "gold_master"
        / "account_opening_full.json"
    ).read_text()
)


async def main() -> None:
    tools = await server.list_tools()
    print("Registered MCP tools:", [t.name for t in tools])

    async def call(name, args):
        result = await server.call_tool(name, args)
        # FastMCP returns a (content, structured) tuple or content blocks;
        # pull the first text payload for display.
        content = result[0] if isinstance(result, tuple) else result
        text = content[0].text if content else ""
        return text

    print(
        "list_message_types  ->",
        (await call("list_message_types", {}))[:60],
        "…",
    )
    print(
        "validate_identifier ->",
        await call(
            "validate_identifier",
            {"kind": "lei", "value": "5493001KJTIIGC8Y1R12"},
        ),
    )
    xml = await call(
        "generate_message",
        {"message_type": "acmt.007.001.05", "records": record},
    )
    print("generate_message    ->", xml[:46], "…")


asyncio.run(main())
