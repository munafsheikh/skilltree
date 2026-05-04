"""stdio transport for MCP."""

from __future__ import annotations

import asyncio
import logging
import sys

from mcp.server.stdio import stdio_server

from skilltree.server import SkillTreeServer

logger = logging.getLogger(__name__)


async def run_stdio(registry_config: dict | None = None) -> None:
    """Run the MCP server over stdio."""
    server = SkillTreeServer()
    await server.initialize()

    async with stdio_server() as (read_stream, write_stream):
        await server.mcp.run(
            read_stream,
            write_stream,
            server.mcp.create_initialization_options(),
        )
