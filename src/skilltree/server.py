"""MCP server implementation for skilltree."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import (
    ListResourcesRequest,
    ListResourceTemplatesRequest,
    ListToolsRequest,
    ReadResourceRequestParams,
    Resource,
    TextContent,
    Tool,
)

from skilltree.models import Scope
from skilltree.registry import SkillRegistry
from skilltree.search import SearchIndex

logger = logging.getLogger(__name__)

APP_NAME = "skilltree"
APP_VERSION = "0.1.0"


class SkillTreeServer:
    """MCP server exposing skilltree functionality."""

    def __init__(self, registry: SkillRegistry | None = None) -> None:
        self.registry = registry or SkillRegistry()
        self.search_index = SearchIndex()
        self._mcp = Server(APP_NAME)
        self._setup_handlers()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> None:
        """Scan filesystem and build search index."""
        self.registry.refresh()
        self.search_index.build(self.registry.list_all())
        logger.info("Server initialized with %d skills", len(self.registry.list_all()))

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _setup_handlers(self) -> None:
        @self._mcp.list_tools()
        async def list_tools(_params: ListToolsRequest | None = None) -> list[Tool]:
            return [
                Tool(
                    name="list_skills",
                    description="List skills with optional scope/tag filter",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope": {
                                "type": "string",
                                "enum": [s.value for s in Scope],
                                "description": "Filter by scope",
                            },
                            "tag": {
                                "type": "string",
                                "description": "Filter by tag",
                            },
                        },
                    },
                ),
                Tool(
                    name="search_skills",
                    description="Search skills by keyword query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results",
                                "default": 20,
                            },
                        },
                        "required": ["query"],
                    },
                ),
                Tool(
                    name="get_skill",
                    description="Get full details of a single skill including origin info",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Skill ID or URI",
                            },
                        },
                        "required": ["id"],
                    },
                ),
                Tool(
                    name="get_skill_tree",
                    description="Get hierarchical skill tree",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope": {
                                "type": "string",
                                "enum": [s.value for s in Scope],
                                "description": "Scope to list; omit for all",
                            },
                        },
                    },
                ),
                Tool(
                    name="compare_skill",
                    description="Compare installed vs available vs origin version",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Skill ID or URI",
                            },
                        },
                        "required": ["id"],
                    },
                ),
                Tool(
                    name="install_skill",
                    description="Mark a skill as installed (records version)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Skill ID or URI",
                            },
                            "path": {
                                "type": "string",
                                "description": "Optional install path",
                            },
                        },
                        "required": ["id"],
                    },
                ),
                Tool(
                    name="check_updates",
                    description="Check skill origins for newer versions available remotely",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Specific skill ID to check; omit to check all",
                            },
                        },
                    },
                ),
                Tool(
                    name="list_outdated",
                    description="List skills whose origin reports a newer version",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="sync_skill",
                    description=(
                        "Update a skill's local metadata from its origin "
                        "(records remote version/hash)"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Skill ID or URI to sync",
                            },
                        },
                        "required": ["id"],
                    },
                ),
                Tool(
                    name="refresh",
                    description="Re-scan skill directories and rebuild index",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self._mcp.call_tool()
        async def call_tool(
            name: str, arguments: dict[str, Any] | None = None
        ) -> list[TextContent]:
            args = arguments or {}
            logger.debug("Tool call: %s(%s)", name, args)

            if name == "list_skills":
                return self._tool_list_skills(args)
            elif name == "search_skills":
                return self._tool_search_skills(args)
            elif name == "get_skill":
                return self._tool_get_skill(args)
            elif name == "get_skill_tree":
                return self._tool_get_skill_tree(args)
            elif name == "compare_skill":
                return self._tool_compare_skill(args)
            elif name == "install_skill":
                return self._tool_install_skill(args)
            elif name == "check_updates":
                return await self._tool_check_updates(args)
            elif name == "list_outdated":
                return self._tool_list_outdated()
            elif name == "sync_skill":
                return await self._tool_sync_skill(args)
            elif name == "refresh":
                await self.initialize()
                return [TextContent(type="text", text="Registry refreshed.")]
            else:
                raise ValueError(f"Unknown tool: {name}")

        @self._mcp.list_resources()
        async def list_resources(_params: ListResourcesRequest | None = None) -> list[Resource]:
            resources: list[Resource] = []
            for skill in self.registry.list_all():
                resources.append(
                    Resource(
                        uri=skill.uri,
                        name=skill.name,
                        description=skill.description,
                        mimeType="text/markdown",
                    )
                )
            return resources

        @self._mcp.list_resource_templates()
        async def list_resource_templates(
            _params: ListResourceTemplatesRequest | None = None,
        ) -> list[Any]:
            return []

        @self._mcp.read_resource()
        async def read_resource(params: ReadResourceRequestParams) -> str | bytes:
            uri = params.uri
            skill = self.registry.get_by_uri(uri)
            if skill is None:
                # Try raw id fallback
                skill = self.registry.get(uri.replace("skill://", "").split("/", 1)[-1])
            if skill is None:
                raise ValueError(f"Skill not found: {uri}")
            return skill.content

    # ------------------------------------------------------------------
    # Tool implementations
    # ------------------------------------------------------------------

    def _tool_list_skills(self, args: dict[str, Any]) -> list[TextContent]:
        scope_str = args.get("scope")
        tag = args.get("tag")

        if scope_str:
            scope = Scope(scope_str)
            skills = self.registry.list_by_scope(scope)
        elif tag:
            skills = self.registry.list_by_tag(tag)
        else:
            skills = self.registry.list_all()

        data = [s.to_dict() for s in skills]
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    def _tool_search_skills(self, args: dict[str, Any]) -> list[TextContent]:
        query = args.get("query", "")
        limit = args.get("limit", 20)

        # Use inverted index for tokenized search, fallback to substring
        indexed = self.search_index.query(query)
        if indexed:
            results = []
            for sid, score in indexed[:limit]:
                skill = self.registry.get(sid)
                if skill:
                    d = skill.to_dict()
                    d["_search_score"] = round(score, 3)
                    results.append(d)
        else:
            skills = self.registry.search(query)[:limit]
            results = [s.to_dict() for s in skills]

        return [TextContent(type="text", text=json.dumps(results, indent=2))]

    def _tool_get_skill(self, args: dict[str, Any]) -> list[TextContent]:
        skill_id = args.get("id", "")
        skill = self.registry.get_by_uri(skill_id) or self.registry.get(skill_id)
        if skill is None:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]
        return [TextContent(type="text", text=json.dumps(skill.to_dict(), indent=2))]

    def _tool_get_skill_tree(self, args: dict[str, Any]) -> list[TextContent]:
        scope_str = args.get("scope")
        scope = Scope(scope_str) if scope_str else None
        tree = self.registry.get_tree(scope)
        return [TextContent(type="text", text=json.dumps(tree.to_dict(), indent=2))]

    def _tool_compare_skill(self, args: dict[str, Any]) -> list[TextContent]:
        skill_id = args.get("id", "")
        skill = self.registry.get_by_uri(skill_id) or self.registry.get(skill_id)
        if skill is None:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]

        result = {
            "id": skill.id,
            "local_version": str(skill.version),
            "installed_version": str(skill.installed_version) if skill.installed_version else None,
            "remote_version": str(skill.remote_version) if skill.remote_version else None,
            "has_local_update": skill.has_local_update(),
            "has_origin_update": skill.has_origin_update(),
            "origin": skill.origin,
            "origin_type": skill.origin_type.value,
            "origin_ref": skill.origin_ref,
            "content_hash": skill.content_hash,
            "remote_hash": skill.remote_hash,
            "last_checked": skill.last_checked.isoformat() if skill.last_checked else None,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    def _tool_install_skill(self, args: dict[str, Any]) -> list[TextContent]:
        skill_id = args.get("id", "")
        path = args.get("path")
        skill = self.registry.get_by_uri(skill_id) or self.registry.get(skill_id)
        if skill is None:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]

        install_path = Path(path) if path else None
        self.registry.mark_installed(skill.id, install_path)
        self.registry.save_installed_state()

        result = {
            "id": skill.id,
            "installed_version": str(skill.version),
            "path": str(install_path) if install_path else None,
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _tool_check_updates(self, args: dict[str, Any]) -> list[TextContent]:
        skill_id = args.get("id")
        if skill_id:
            try:
                result = await self.registry.check_origin(skill_id)
            except KeyError:
                return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]
            data = {
                "skill_id": result.skill_id,
                "origin": result.origin,
                "origin_type": result.origin_type.value,
                "is_accessible": result.is_accessible,
                "is_outdated": result.is_outdated,
                "remote_version": str(result.remote_version) if result.remote_version else None,
                "remote_hash": result.remote_hash,
                "error": result.error,
                "checked_at": result.checked_at.isoformat(),
            }
            return [TextContent(type="text", text=json.dumps(data, indent=2))]
        else:
            results = await self.registry.check_origins()
            data = [
                {
                    "skill_id": r.skill_id,
                    "origin": r.origin,
                    "origin_type": r.origin_type.value,
                    "is_accessible": r.is_accessible,
                    "is_outdated": r.is_outdated,
                    "remote_version": str(r.remote_version) if r.remote_version else None,
                    "remote_hash": r.remote_hash,
                    "error": r.error,
                    "checked_at": r.checked_at.isoformat(),
                }
                for r in results
            ]
            return [TextContent(type="text", text=json.dumps(data, indent=2))]

    def _tool_list_outdated(self) -> list[TextContent]:
        skills = self.registry.list_outdated()
        data = [s.to_dict() for s in skills]
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    async def _tool_sync_skill(self, args: dict[str, Any]) -> list[TextContent]:
        skill_id = args.get("id", "")
        skill = self.registry.get_by_uri(skill_id) or self.registry.get(skill_id)
        if skill is None:
            return [TextContent(type="text", text=json.dumps({"error": "Not found"}))]

        result = await self.registry.check_origin(skill.id)
        data = {
            "id": skill.id,
            "synced": result.is_accessible,
            "is_outdated": result.is_outdated,
            "local_version": str(skill.version),
            "remote_version": str(skill.remote_version) if skill.remote_version else None,
            "remote_hash": skill.remote_hash,
            "last_checked": skill.last_checked.isoformat() if skill.last_checked else None,
            "error": result.error,
        }
        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    # ------------------------------------------------------------------
    # Accessors for transport runners
    # ------------------------------------------------------------------

    @property
    def mcp(self) -> Server:
        return self._mcp
