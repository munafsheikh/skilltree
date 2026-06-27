# Roadmap / Further Development

This is a living list of directions for the project. Not commitments or a fixed order — pick items up via PRs, and feel free to propose new ones through an issue.

## Near-term

- **Persistent search index** — currently `SearchIndex` rebuilds in memory on every server start; large skill sets would benefit from an on-disk cache invalidated by content hash.
- **Skill validation CLI** — a `skilltree-mcp validate` (or pre-commit hook) that lints `SKILL.md` frontmatter (required fields, valid semver, tag conventions) before merge.
- **Pagination for `list_skills`/`search_skills`** — needed once the built-in tree grows well beyond its current ~50 skills.
- **Structured logging** — replace ad-hoc prints with a configurable logger, especially for the SSE transport and origin checkers.

## Medium-term

- **Authentication for the SSE/HTTP transport** — token-based auth for multi-tenant or public deployments (currently assumes a trusted network).
- **Skill dependency resolution** — `dependencies` is currently metadata-only; resolve and surface unmet dependencies when installing a skill.
- **Pluggable origin checkers** — formalize a registration mechanism so third parties can add origin types (e.g. npm, PyPI, OCI registries) without modifying `origins.py` directly.
- **Web UI** — a lightweight browser-based tree/search view served alongside the SSE transport, for human exploration without an MCP client.

## Long-term / exploratory

- **Multi-server federation** — let one skilltree instance proxy/aggregate skills from other skilltree servers (composable registries).
- **Skill versioning with changelogs** — richer version history per skill, not just current vs. origin version.
- **Usage analytics (opt-in)** — track which skills are actually fetched/installed by clients to inform curation of the built-in set.
- **Package manager integration** — publish to PyPI under a stable name and explore a Homebrew/apt distribution path for the CLI.

## How to propose changes to this roadmap

Open an issue describing the motivation and rough approach. If you intend to implement something here, mention it in the issue first to avoid duplicate work, then follow [CONTRIBUTING.md](../CONTRIBUTING.md).
