# seoji CLI and server: `docker run IMAGE serve` (default), `harvest …`, `db migrate`, ...
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
# `seoji db migrate` reads <repo root>/migrations next to src/ (seoji.db.MIGRATIONS_DIR).
COPY migrations ./migrations
RUN uv sync --frozen --no-dev

USER 10001:10001
ENTRYPOINT ["seoji"]
CMD ["serve", "--host", "0.0.0.0"]
