"""CLI entry point for skilltree-mcp."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from skilltree.registry import RegistryConfig, Scope, SkillRegistry
from skilltree.transport import run_sse, run_stdio


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _build_registry_config(args: argparse.Namespace) -> RegistryConfig:
    cfg = RegistryConfig()
    if args.built_in_root:
        cfg.roots[Scope.BUILT_IN] = [Path(p) for p in args.built_in_root]
    if args.extra_root:
        cfg.roots[Scope.EXTRA] = [Path(p) for p in args.extra_root]
    if args.user_root:
        cfg.roots[Scope.USER] = [Path(p) for p in args.user_root]
    if args.project_root:
        cfg.roots[Scope.PROJECT] = [Path(p) for p in args.project_root]
    return cfg


def _origin_marker(skill) -> str:
    markers = []
    if skill.has_local_update():
        markers.append("local-update")
    if skill.is_outdated:
        markers.append("origin-update")
    if markers:
        return " [" + ", ".join(markers) + "]"
    return ""


def cmd_list(args: argparse.Namespace) -> int:
    """List skills (non-MCP, direct CLI)."""
    _setup_logging(args.verbose)
    cfg = _build_registry_config(args)
    reg = SkillRegistry(cfg)
    reg.refresh()

    scope = Scope(args.scope) if args.scope else None
    if scope:
        skills = reg.list_by_scope(scope)
    elif args.tag:
        skills = reg.list_by_tag(args.tag)
    else:
        skills = reg.list_all()

    if args.format == "json":
        print(json.dumps([s.to_dict() for s in skills], indent=2))
    else:
        for s in skills:
            print(f"{s.scope.value:10} {s.id:40} v{s.version}{_origin_marker(s)}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search skills (non-MCP, direct CLI)."""
    _setup_logging(args.verbose)
    cfg = _build_registry_config(args)
    reg = SkillRegistry(cfg)
    reg.refresh()

    skills = reg.search(args.query)[: args.limit]
    if args.format == "json":
        print(json.dumps([s.to_dict() for s in skills], indent=2))
    else:
        for s in skills:
            print(f"{s.scope.value:10} {s.id:40} {s.name}")
    return 0


def cmd_tree(args: argparse.Namespace) -> int:
    """Show skill tree (non-MCP, direct CLI)."""
    _setup_logging(args.verbose)
    cfg = _build_registry_config(args)
    reg = SkillRegistry(cfg)
    reg.refresh()

    scope = Scope(args.scope) if args.scope else None
    tree = reg.get_tree(scope)
    print(json.dumps(tree.to_dict(), indent=2))
    return 0


def cmd_outdated(args: argparse.Namespace) -> int:
    """List outdated skills."""
    _setup_logging(args.verbose)
    cfg = _build_registry_config(args)
    reg = SkillRegistry(cfg)
    reg.refresh()

    skills = reg.list_outdated()
    if args.format == "json":
        print(json.dumps([s.to_dict() for s in skills], indent=2))
    else:
        for s in skills:
            print(f"{s.id:40} local={s.version} origin={s.remote_version} {s.origin}")
    return 0


async def _cmd_check_updates(args: argparse.Namespace) -> int:
    """Check skill origins for updates."""
    _setup_logging(args.verbose)
    cfg = _build_registry_config(args)
    reg = SkillRegistry(cfg)
    reg.refresh()

    if args.id:
        try:
            result = await reg.check_origin(args.id)
        except KeyError:
            print(f"Skill not found: {args.id}", file=sys.stderr)
            return 1
        results = [result]
    else:
        results = await reg.check_origins()

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
        }
        for r in results
    ]
    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        for r in results:
            status = "OUTDATED" if r.is_outdated else "ok"
            if not r.is_accessible:
                status = f"ERROR: {r.error}"
            print(f"{r.skill_id:40} {status:20} {r.origin}")
    return 0


def cmd_check_updates(args: argparse.Namespace) -> int:
    return asyncio.run(_cmd_check_updates(args))


def cmd_stdio(args: argparse.Namespace) -> int:
    """Run MCP over stdio."""
    _setup_logging(args.verbose)
    asyncio.run(run_stdio())
    return 0


def cmd_sse(args: argparse.Namespace) -> int:
    """Run MCP over SSE/HTTP."""
    _setup_logging(args.verbose)
    asyncio.run(run_sse(host=args.host, port=args.port))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="skilltree-mcp",
        description="Skilltree MCP server and CLI",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--built-in-root",
        action="append",
        help="Override built-in skill root (repeatable)",
    )
    parser.add_argument(
        "--extra-root",
        action="append",
        help="Override extra skill root (repeatable)",
    )
    parser.add_argument(
        "--user-root",
        action="append",
        help="Override user skill root (repeatable)",
    )
    parser.add_argument(
        "--project-root",
        action="append",
        help="Override project skill root (repeatable)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List skills")
    p_list.add_argument("--scope", choices=[s.value for s in Scope], help="Filter by scope")
    p_list.add_argument("--tag", help="Filter by tag")
    p_list.add_argument("--format", choices=["text", "json"], default="text")
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = sub.add_parser("search", help="Search skills")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--format", choices=["text", "json"], default="text")
    p_search.set_defaults(func=cmd_search)

    # tree
    p_tree = sub.add_parser("tree", help="Show skill tree")
    p_tree.add_argument("--scope", choices=[s.value for s in Scope], help="Filter by scope")
    p_tree.set_defaults(func=cmd_tree)

    # outdated
    p_outdated = sub.add_parser("outdated", help="List skills with origin updates available")
    p_outdated.add_argument("--format", choices=["text", "json"], default="text")
    p_outdated.set_defaults(func=cmd_outdated)

    # check-updates
    p_check = sub.add_parser("check-updates", help="Check skill origins for newer versions")
    p_check.add_argument("--id", help="Check a specific skill ID")
    p_check.add_argument("--format", choices=["text", "json"], default="text")
    p_check.set_defaults(func=cmd_check_updates)

    # stdio
    p_stdio = sub.add_parser("stdio", help="Run MCP stdio server")
    p_stdio.set_defaults(func=cmd_stdio)

    # sse
    p_sse = sub.add_parser("sse", help="Run MCP SSE server")
    p_sse.add_argument("--host", default="0.0.0.0")
    p_sse.add_argument("--port", type=int, default=8080)
    p_sse.set_defaults(func=cmd_sse)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
