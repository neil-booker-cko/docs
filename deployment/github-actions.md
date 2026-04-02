# GitHub Actions: Build & Publish Docker Image

Triggers on push to `main`. Builds the Docker image and pushes to GitHub Container
Registry (ghcr.io) tagged with both `latest` and the commit SHA.

## Prerequisites

- GitHub Container Registry is enabled for your organisation/account (enabled by default)
- No additional secrets required — uses the built-in `GITHUB_TOKEN`

## Workflow

Save as `.github/workflows/publish.yml`:

```yaml
name: Publish docs image

on:
  push:
    branches: [main]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=registry,ref=ghcr.io/${{ github.repository }}:latest
          cache-to: type=inline
```

## Image reference for Watchtower

```text
ghcr.io/<org-or-user>/<repo>:latest
```

## Notes

- The `cache-from` / `cache-to` lines reuse the previous `latest` layer cache, keeping
  build times short after the first run.
- The SHA tag gives you a pinnable reference for rollback:
  `docker pull ghcr.io/<org>/<repo>:<sha>`
- To make the image publicly accessible: **Packages → Change visibility → Public**,
  otherwise Watchtower will need a Personal Access Token (PAT) with `read:packages`
  scope configured as a registry credential.
