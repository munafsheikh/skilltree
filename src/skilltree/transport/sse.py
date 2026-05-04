"""SSE / HTTP transport for MCP."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from uvicorn.main import run as uvicorn_run

from skilltree.server import SkillTreeServer

logger = logging.getLogger(__name__)


async def run_sse(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Run the MCP server over SSE/HTTP."""
    server = SkillTreeServer()
    await server.initialize()

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Any:
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await server.mcp.run(
                read_stream,
                write_stream,
                server.mcp.create_initialization_options(),
            )

    async def handle_health(_request: Request) -> JSONResponse:
        return JSONResponse({
            "status": "ok",
            "skills": len(server.registry.list_all()),
            "version": server.mcp.name,
        })

    async def handle_skills(request: Request) -> JSONResponse:
        scope = request.query_params.get("scope")
        tag = request.query_params.get("tag")
        if scope:
            from skilltree.models import Scope
            skills = server.registry.list_by_scope(Scope(scope))
        elif tag:
            skills = server.registry.list_by_tag(tag)
        else:
            skills = server.registry.list_all()
        return JSONResponse([s.to_dict() for s in skills])

    async def handle_search(request: Request) -> JSONResponse:
        q = request.query_params.get("q", "")
        limit = int(request.query_params.get("limit", "20"))
        skills = server.registry.search(q)[:limit]
        return JSONResponse([s.to_dict() for s in skills])

    app = Starlette(
        debug=False,
        routes=[
            Route("/", handle_health),
            Route("/sse", handle_sse),
            Route("/skills", handle_skills),
            Route("/search", handle_search),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    uvicorn_run(app, host=host, port=port, log_level="info")
