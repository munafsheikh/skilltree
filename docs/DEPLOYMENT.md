# Deployment

skilltree can run as a local stdio MCP server (no network exposure) or as a long-running SSE/HTTP service. Use stdio for desktop MCP clients (Claude Desktop, Cursor, etc.) and SSE for shared/remote deployments.

## Stdio (local, per-client)

No deployment needed — the client launches the process:

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

## SSE/HTTP (shared server)

```bash
skilltree-mcp sse --host 0.0.0.0 --port 8080
```

Endpoints exposed by the SSE transport (`src/skilltree/transport/sse.py`):

| Route | Purpose |
|---|---|
| `GET /` | Health check (status, skill count, version) |
| `GET /sse` | MCP SSE connection |
| `GET /skills?scope=&tag=` | JSON skill listing |
| `GET /search?q=&limit=` | JSON search results |
| `POST /messages/*` | MCP message handling |

## Docker

### Build & run with docker-compose (recommended)

```bash
docker compose up --build -d
```

`docker-compose.yml` provides:
- Port mapping `8080:8080`
- `SKILLTREE_HOST=0.0.0.0`, `SKILLTREE_PORT=8080`
- A read-only volume mount for external skills
- A named volume (`skilltree-state`) for persisting installed/origin state across restarts
- An HTTP health check every 30s
- `restart: unless-stopped`

### Build & run manually

```bash
docker build -t skilltree .
docker run -d \
  -p 8080:8080 \
  -v ./skills:/app/skills:ro \
  -v skilltree-state:/root/.config/skilltree \
  --restart unless-stopped \
  skilltree
```

The image is a multi-stage build (`Dockerfile`): a `builder` stage installs the package with `uv`, and a slim `python:3.13-slim` runtime stage copies only the installed site-packages. The entrypoint runs `skilltree-mcp sse --host 0.0.0.0 --port 8080`.

### Mounting extra/user/project skills

Skill scopes resolve from filesystem roots that can be bind-mounted into the container:

```bash
docker run -d -p 8080:8080 \
  -v ./extra-skills:/app/extra:ro \
  -v ./user-skills:/app/user:ro \
  skilltree skilltree-mcp sse --extra-root /app/extra --user-root /app/user
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `SKILLTREE_HOST` | `127.0.0.1` | SSE server bind address |
| `SKILLTREE_PORT` | `8080` | SSE server port |

CLI flags (`--built-in-root`, `--extra-root`, `--user-root`, `--project-root`, `--verbose`) override the default scope roots; see `skilltree-mcp --help`.

## State persistence

Installed-skill state and origin-check state are persisted to:

- `~/.config/skilltree/installed.json`
- `~/.config/skilltree/origins.json`

In Docker, mount a volume over `/root/.config/skilltree` (as in the compose file) so this state survives container restarts.

## Releasing a new version

1. Bump the version in `pyproject.toml` and `src/skilltree/__init__.py`.
2. Tag the commit: `git tag vX.Y.Z && git push origin vX.Y.Z`.
3. The CI `release` job builds the package and publishes a GitHub Release with generated notes once `build` and `test-wheel` pass.
