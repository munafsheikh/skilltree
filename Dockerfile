# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
RUN mkdir -p src/skilltree && touch src/skilltree/__init__.py
RUN uv pip install --system -e "."

COPY . .
RUN uv pip install --system -e "."

# ---
FROM python:3.13-slim AS runtime

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV SKILLTREE_HOST=0.0.0.0
ENV SKILLTREE_PORT=8080

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app .

EXPOSE 8080

ENTRYPOINT ["skilltree-mcp"]
CMD ["sse", "--host", "0.0.0.0", "--port", "8080"]
