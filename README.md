# skilltree

An MCP (Model Context Protocol) server that exposes a searchable, versioned, hierarchical tree of skills for AI tools to discover, compare, download, and install.

## What is skilltree?

skilltree is a universal **self-hosted skill registry**. The MCP server **provides the skills itself** — they are embedded in the package — so any MCP-compatible client (Claude Desktop, Cursor, Kimi, custom agents, etc.) can browse, search, compare, and install skills without relying on external filesystem paths.

Skills are Markdown files (`SKILL.md`) organized in a directory hierarchy. Each skill carries metadata (name, description, version, tags, dependencies) and can live in one of four scopes:

| Scope | Precedence | Source |
|---|---|---|
| `built-in` | lowest | **Embedded in the server package** — always available |
| `extra` | low | Optional community packs from filesystem |
| `user` | medium | `~/.config/agents/skills/`, `~/.claude/skills/` (optional override) |
| `project` | highest | `./.skills/` in your project (optional override) |

Higher-precedence scopes can override or extend lower ones, but the **server is the primary source** — it ships with a comprehensive skill tree out of the box.

## Features

- **Hierarchical skill trees** — skills nest in directories; trees are exposed as MCP resources
- **Full-text search** — inverted index with relevance scoring across names, descriptions, tags, and content
- **Origin tracking** — every skill knows its source (git, HTTP, embedded, local) and can be checked for remote updates
- **Version comparison** — semantic versioning with installed vs local vs origin diff
- **Installation tracking** — record which skills are installed and at what version
- **Multiple transports** — stdio (local), SSE/HTTP (remote/Docker), and a native REST API
- **Docker support** — one-command containerized deployment
- **CLI** — query, explore, and check origins without an MCP client

## Quick Start

### Install

```bash
pip install -e "."
```

### Run stdio MCP (for Claude Desktop, etc.)

```bash
skilltree-mcp stdio
```

Add to your MCP client config:

```json
{
  "mcpServers": {
    "skilltree": {
      "command": "skilltree-mcp",
      "args": ["stdio"]
    }
  }
}
```

### Run SSE/HTTP server

```bash
skilltree-mcp sse --host 0.0.0.0 --port 8080
```

Then connect via SSE at `http://localhost:8080/sse`.

### Docker

```bash
docker compose up --build
```

Or manually:

```bash
docker build -t skilltree .
docker run -p 8080:8080 -v ./skills:/app/skills:ro skilltree
```

### CLI usage

```bash
# List all skills
skilltree-mcp list

# Search
skilltree-mcp search docker

# Show tree
skilltree-mcp tree

# Check origins for updates
skilltree-mcp check-updates

# List only outdated skills
skilltree-mcp outdated

# JSON output
skilltree-mcp list --format json
```

## MCP Tools

| Tool | Description |
|---|---|
| `list_skills` | List skills with optional scope/tag filter |
| `search_skills` | Full-text search with relevance scoring |
| `get_skill` | Get full details and metadata of a skill |
| `get_skill_tree` | Return hierarchical tree structure |
| `compare_skill` | Compare installed vs local vs origin version |
| `install_skill` | Mark a skill as installed (tracks version) |
| `check_updates` | Check skill origins for newer remote versions |
| `list_outdated` | List skills whose origin reports a newer version |
| `sync_skill` | Sync a skill's metadata from its origin |
| `refresh` | Re-scan skill directories and rebuild index |

## MCP Resources

Every skill is exposed as a readable MCP resource:

- `skill://built-in/docker-expert` — read the Docker Expert skill content
- `skill://user/my-custom-skill` — read a user-defined skill

## Skill Format

A skill is a directory containing at least `SKILL.md`:

```text
src/skilltree/skills/built-in/devops/docker/
├── SKILL.md
└── skill.json      # optional sidecar metadata
```

`SKILL.md` frontmatter:

```markdown
---
name: Docker Expert
description: Advanced Docker containerization...
version: 2.1.0
tags: [docker, container, devops, security]
dependencies: []
origin_type: embedded
metadata:
  author: skilltree
  license: MIT
---

# Docker Expert

Your Markdown content here...
```

### Origin metadata

Skills can declare where they come from so the server can check for updates:

| Field | Values | Description |
|---|---|---|
| `origin_type` | `embedded`, `git`, `http`, `local` | How to check for updates |
| `origin` | URL or path | Git repo URL, HTTP endpoint, or filesystem path |
| `origin_ref` | branch, tag, or sub-URL | Git ref or manifest URL to query |

## Project Structure

```
skilltree/
├── src/skilltree/         # MCP server & registry
│   ├── server.py          # MCP server with tools & resources
│   ├── registry.py        # Skill discovery & management
│   ├── models.py          # Data models (Skill, SkillTree, SemVer, Scope)
│   ├── search.py          # Inverted index search
│   ├── transport/         # stdio & SSE transports
│   ├── cli.py             # CLI entry point
│   └── skills/            # **Embedded built-in skill tree**
│       └── built-in/
│           ├── software-engineering/
│           ├── languages/
│           ├── devops/
│           ├── cloud/
│           ├── data-engineering/
│           ├── security/
│           ├── ai-ml/
│           ├── productivity/
│           ├── communication/
│           └── project-management/
├── tests/                 # pytest suite
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SKILLTREE_HOST` | `127.0.0.1` | SSE server bind address |
| `SKILLTREE_PORT` | `8080` | SSE server port |

## Contributing Skills

Add skills under `src/skilltree/skills/built-in/` (embedded in the package) or any configured filesystem root. Run `skilltree-mcp refresh` (or the `refresh` MCP tool) to pick them up.

## License

MIT
