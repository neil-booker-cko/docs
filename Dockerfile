# Stage 1: build the static site
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .
RUN uv run mkdocs build --strict

# Stage 2: serve with nginx
FROM nginx:alpine

COPY --from=builder /build/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
