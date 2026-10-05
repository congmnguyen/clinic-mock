# syntax=docker/dockerfile:1.7
# uv-first build: dependency resolution and venv management both go through uv.
FROM python:3.13-slim AS builder

# Install uv from the official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Railway's builder accepts only service-scoped cache mounts, so no mounts here:
# dependencies first (layer-cached), then the project itself.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev
COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime

# Create non-root user before any file copies so we can chown cleanly.
RUN useradd --create-home --shell /bin/bash --uid 10001 appuser

# Carry the resolved venv and uv into the runtime image.
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /bin/uv /bin/uvx /bin/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY --chown=appuser:appuser src ./src

EXPOSE 8000

# Run the installed `prod` script (entry point from pyproject.toml).
# Same as `uv run prod` — uses the venv and respects settings.app.HOST/PORT.
USER appuser
CMD ["uv", "run", "prod"]
