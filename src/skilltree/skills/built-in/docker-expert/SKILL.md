---
name: Docker Expert
description: Advanced Docker containerization, optimization, and orchestration.
version: 2.1.0
tags: [docker, container, orchestration, devops, security]
dependencies: []
metadata:
  author: skilltree
  license: MIT
---

# Docker Expert

## Multi-Stage Builds

Always use multi-stage builds to minimize image size:

```dockerfile
FROM python:3.13-slim AS builder
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv pip install --system -e "."

FROM python:3.13-slim AS runtime
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
```

## Security Hardening

- Run containers as non-root
- Use read-only root filesystems
- Scan images with Trivy or Snyk
- Pin base image digests
