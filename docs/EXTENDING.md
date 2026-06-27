# Extending skilltree

## Architecture overview

| Module | Responsibility |
|---|---|
| `src/skilltree/models.py` | Core data types: `Skill`, `SkillTree`, `SemVer`, `Scope`, `OriginType` |
| `src/skilltree/registry.py` | `SkillRegistry` — scans filesystem roots, loads skills, persists installed/origin state |
| `src/skilltree/search.py` | `SearchIndex` — in-memory inverted index with relevance scoring |
| `src/skilltree/origins.py` | `OriginChecker` implementations (embedded, local, git, http) and async update checking |
| `src/skilltree/server.py` | `SkillTreeServer` — wires the registry/search into MCP tools and resources |
| `src/skilltree/transport/` | `stdio.py` and `sse.py` — how the server is exposed to clients |
| `src/skilltree/cli.py` | `skilltree-mcp` command-line entry point |
| `src/skilltree/skills/built-in/` | Embedded skill content shipped with the package |

Request flow: a transport (stdio or SSE) receives an MCP call → `SkillTreeServer` dispatches to a tool handler → the handler calls into `SkillRegistry` (and `SearchIndex` for search) → results are returned as MCP tool responses or resource reads.

## Adding a new built-in skill

1. Create a directory under `src/skilltree/skills/built-in/<category>/<skill-id>/` containing `SKILL.md`.
2. Add YAML frontmatter:

   ```markdown
   ---
   name: My New Skill
   description: One-line summary of what this teaches.
   version: 1.0.0
   tags: [tag1, tag2]
   dependencies: []
   origin_type: embedded
   metadata:
     author: skilltree
     license: MIT
   ---

   # My New Skill

   Full Markdown content here.
   ```

3. Optionally add a `skill.json` sidecar to override metadata without editing frontmatter.
4. If you maintain skills generated programmatically, add an entry to `scripts/generate_skills.py`'s `SKILLS` dict and re-run it.
5. Run `skilltree-mcp refresh` (or call the `refresh` MCP tool) to pick up the new skill without restarting, or just restart the server.
6. Add/extend a test in `tests/test_registry.py` if the skill exercises new registry behavior.

## Adding a new scope or root

Scopes are defined in `models.Scope` with explicit precedence (`built-in` < `extra` < `user` < `project`). To add a new scope:

1. Add a member to the `Scope` enum and update `precedence()`.
2. Add a corresponding root option in `RegistryConfig` (`registry.py`) and a CLI flag in `cli.py`.
3. Update `SkillRegistry.scan()` to include the new root.

Most extension scenarios don't need a new scope — `extra`/`user`/`project` roots already support mounting arbitrary filesystem trees (see [DEPLOYMENT.md](DEPLOYMENT.md)).

## Adding a new origin checker

Origin checkers let skilltree detect when a skill's upstream source has a newer version.

1. Subclass `OriginChecker` in `origins.py` and implement the check method, returning an `OriginCheckResult`.
2. Register it for the relevant `OriginType` in the dispatch used by `check_skill_origin`.
3. If the check is network-bound, make it `async` and use `anyio` for concurrency, following `GitOriginChecker`/`HTTPOriginChecker`.
4. Add a test in `tests/test_origins.py`, mocking the network/filesystem call.

## Adding a new MCP tool

1. Implement the handler in `server.py` (`SkillTreeServer`), following the pattern of existing tools (e.g. `list_skills`).
2. Register the tool's schema (name, description, input schema) alongside the others in the server's tool list.
3. If the tool should also be reachable via CLI, add a subcommand in `cli.py`.
4. If it should be reachable over plain HTTP, add a route in `transport/sse.py`.
5. Document it in the README's MCP Tools table.

## Adding a new transport

Implement a new module under `src/skilltree/transport/` that adapts `SkillTreeServer` to the new protocol, mirroring `stdio.py` (wraps `mcp.server.stdio_server()`) or `sse.py` (Starlette app). Wire it into a new `cli.py` subcommand.

## Code style

- Ruff handles linting and formatting — run `ruff check` and `ruff format` before committing.
- `mypy` runs in strict mode; new code should be fully typed.
- Keep modules focused: registry logic stays in `registry.py`, MCP-specific wiring stays in `server.py`.
