# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Network Resilience Library** is a MkDocs-based technical documentation site for network engineering
 focusing on sub-second failover and hybrid-cloud connectivity. Content covers Cisco IOS-XE, Fortinet
 FortiGate, and cloud providers (AWS, Azure, GCP).

## Development Commands

```bash
# Start local preview server
uv run mkdocs serve

# Build static site (generates site/ directory)
uv run mkdocs build

# Run pre-commit hooks manually
pre-commit run --all-files

# Update dependencies
uv sync --all-groups
```

## Key Configuration Files

| File | Purpose |
| --- | --- |
| `mkdocs.yml` | Site structure, theme config, markdown extensions |
| `.markdownlint-cli2.yaml` | Markdown linting rules (88 char line length, H1 requirement, duplicate headings allowed in different sections) |
| `.pre-commit-config.yaml` | Automated checks: file hygiene, Python formatting (Ruff), markdown linting |
| `hooks.py` | MkDocs hook to minify HTML output (removes leading whitespace) |
| `pyproject.toml` | Dependencies (mkdocs-material, minify plugin) and Python config |

## Documentation Structure

```text
docs/
├── theory/          # Protocol comparisons (BGP vs BFD, OSPF vs EIGRP, etc.)
├── cisco/           # IOS-XE configuration guides
├── fortigate/       # FortiOS configuration guides
├── aws/             # AWS architecture and VPN/BGP designs
├── azure/           # Azure ExpressRoute architecture
├── gcp/             # GCP Cloud Interconnect architecture
├── operations/      # Troubleshooting, upgrades, change verification
├── routing/         # Routing protocols (BGP, OSPF, EIGRP, RIP, IGRP)
├── application/     # Application protocols (DNS, SSH, SNMP, NetFlow, etc.)
├── packets/         # Packet header formats (Ethernet, IPv4/v6, TCP/UDP, BFD, etc.)
└── reference/       # Quick-reference tables (IP ranges, ports, ICMP types, MTU, etc.)
```

## Content Guidelines

**Scope:** Focus on Cisco IOS-XE and FortiGate. Do not add other vendors (Juniper, Arista, etc.).

**Pairing Rules:**

- DSCP and QoS must be paired — do not add DSCP reference without accompanying QoS content
- LLDP and CDP should be documented together in the same section
- MPLS is explicitly out of scope

**Markdown Requirements:**

- Every file must start with a top-level H1 heading (`# Title`)
- Line length: 88 characters max (120 for code blocks, no limit for tables)
- Allowed inline HTML: `<br>`, `<details>`, `<summary>` (for collapsible sections)
- Duplicate heading names allowed only across different sections (e.g., multiple "Examples" headers
    in different docs)

**Architecture Diagrams:** Use Mermaid (supported via `pymdownx.superfences`) for flowcharts, sequence
diagrams, and architecture layouts.

## Pre-Commit Workflow

Pre-commit hooks run automatically on `git commit`. They enforce:

1. **File Hygiene** (fastest): Remove trailing whitespace, fix EOF, normalize line endings, prevent
    large files
2. **Python Formatting** (Ruff): Format and lint any Python files (hooks.py)
3. **Markdown Linting**: Validate structure, line length, headings

Run `pre-commit run --all-files` to test all changes before committing.

## Navigation Structure

The site navigation tree is defined in `mkdocs.yml` under the `nav:` section. Top-level sections are
sticky tabs; subsections expand/collapse. When adding new docs, add corresponding entries to keep the
nav current.

## Deployment

See `DEPLOYMENT.md` for Docker, Traefik, CI/CD (GitHub Actions / GitLab CI), and Watchtower container
auto-update setup.
