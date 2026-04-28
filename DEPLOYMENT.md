# Deployment

This repo builds and serves a static site (built with Zensical) via an nginx container,
with Traefik as the SSL-terminating reverse proxy. CI/CD rebuilds and pushes the image
on every push to `main`; Watchtower handles rolling updates on the host.

---

## Prerequisites

- Docker and Docker Compose
- Traefik running with an internal CA (step-ca) ACME resolver
- Watchtower (optional, for automated updates)

---

## Configuration

Before deploying, update the placeholder values in `docker-compose.yml`:

| Placeholder | Description |
| --- | --- |
| `docs.example.internal` | Hostname Traefik will route to this service |
| `CERT_RESOLVER` | Name of the ACME resolver in your Traefik config |
| `TRAEFIK_NETWORK` | Name of the external Docker network Traefik uses |

---

## Building and running locally

Build the image:

```bash
docker build -t docs .
```

Run with Compose (requires Traefik network to exist):

```bash
docker compose up -d
```

The site is built inside the container at build time — no local `uv run zensical build`
required.

---

## CI/CD

The `deployment/` directory contains pipeline configs for both GitHub and GitLab. Both
pipelines trigger on push to `main`, build the Docker image, and push it to the
platform's container registry tagged with `latest` and the commit SHA.

| Platform | Config | Registry |
| --- | --- | --- |
| GitHub Actions | `deployment/github-actions.md` | `ghcr.io/<org>/<repo>` |
| GitLab CI | `deployment/gitlab-ci.md` | `registry.gitlab.com/<group>/<project>` |

Copy the relevant pipeline file to its required location (`.github/workflows/publish.yml`
or `.gitlab-ci.yml`) and update the image references in `docker-compose.yml` to point
at the registry image rather than building locally.

---

## Automated updates with Watchtower

With CI/CD pushing a new `latest` image on each merge, Watchtower can automatically
redeploy the running container when it detects an updated image.

Configure Watchtower to watch this service by adding a label to `docker-compose.yml`:

```yaml
labels:
  - "com.centurylinklabs.watchtower.enable=true"
```

If the registry is private, configure Watchtower with registry credentials — see the
[Watchtower private registries docs](https://containrrr.dev/watchtower/private-registries/).

---

## Updating pinned versions

The `Dockerfile` pins `uv` and `nginx` to specific versions. To upgrade:

| Component | Location | How to update |
| --- | --- | --- |
| `uv` | `Dockerfile` line 4 | Replace version tag, e.g. `uv:0.11.3` → `uv:x.y.z` |
| `nginx` | `Dockerfile` stage 2 | Uses `nginxinc/nginx-unprivileged:stable-alpine` — rebuilt weekly with security patches; no action needed |
| Pre-commit hooks | `.pre-commit-config.yaml` | Run `pre-commit autoupdate` |
| Python deps | `uv.lock` | Run `uv sync --upgrade` |
