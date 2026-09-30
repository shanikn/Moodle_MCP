# Container image for hosting the Moodle MCP server over HTTP (e.g. Google Cloud Run).
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app

# Install dependencies first (cached layer), then the project itself.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

ENV MCP_TRANSPORT=http
CMD ["/app/.venv/bin/moodle-mcp"]
