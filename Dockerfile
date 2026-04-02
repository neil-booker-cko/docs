# Stage 1: build the static site
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy

WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .
RUN uv run mkdocs build --strict

# Stage 2: serve with nginx
FROM nginx:1.29.7-alpine

COPY --from=builder /build/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
