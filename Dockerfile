# Stage 1: build the static site
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy

WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .
RUN uv run zensical build

# Stage 2: serve with nginx
# Option A: Docker Hardened Images — distroless, signed SBOM, SLSA L3, requires dhi.io login
FROM dhi.io/nginx:1.30-debian12
# Option B: Official nginx unprivileged — Alpine, non-root, no auth required, weekly CVE patches
# FROM nginxinc/nginx-unprivileged:stable-alpine

COPY --from=builder /build/site /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
