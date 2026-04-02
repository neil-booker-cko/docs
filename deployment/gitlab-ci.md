# GitLab CI: Build & Publish Docker Image

Triggers on push to `main`. Builds the Docker image and pushes to the built-in GitLab
Container Registry tagged with both `latest` and the short commit SHA.

## Prerequisites

- Container Registry enabled for your project (enabled by default in GitLab)
- No additional variables required — uses the built-in CI/CD variables
  `CI_REGISTRY`, `CI_REGISTRY_USER`, and `CI_REGISTRY_PASSWORD`

## Pipeline

Save as `.gitlab-ci.yml` at the repository root:

```yaml
stages:
  - publish

publish-image:
  stage: publish
  image: docker:27
  services:
    - docker:27-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      docker build \
        --cache-from $CI_REGISTRY_IMAGE:latest \
        --tag $CI_REGISTRY_IMAGE:latest \
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA \
        .
    - docker push $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

## Image reference for Watchtower

```text
registry.gitlab.com/<group>/<project>:latest
```

## Notes

- `DOCKER_TLS_CERTDIR: "/certs"` is required for Docker-in-Docker (dind) with TLS,
  which is the default in modern GitLab runners.
- The `--cache-from` flag pulls the previous `latest` image as a layer cache before
  building, significantly reducing build time after the first run.
- The SHA tag gives you a pinnable reference for rollback:
  `docker pull registry.gitlab.com/<group>/<project>:<short-sha>`
- For Watchtower to pull from a private GitLab registry, configure a
  [registry credential](https://containrrr.dev/watchtower/private-registries/) using
  a GitLab Deploy Token with `read_registry` scope.
