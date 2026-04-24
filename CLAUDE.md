# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Network Resilience Library** is a MkDocs-based technical documentation site for network engineering
 focusing on sub-second failover and hybrid-cloud connectivity. Content covers Cisco IOS-XE, Fortinet
 FortiGate, cloud providers (AWS, Azure, GCP), and Equinix Fabric Cloud Router for multi-cloud
 interconnection.

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
| `.markdownlint-cli2.yaml` | Markdown linting rules (100 char line length, code blocks/tables unlimited, H1 requirement, duplicate headings allowed in different sections) |
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
├── equinix/         # Equinix Fabric Cloud Router (FCR) and multi-cloud
├── operations/      # Troubleshooting, upgrades, change verification
├── routing/         # Routing protocols (BGP, OSPF, EIGRP, RIP, IGRP)
├── application/     # Application protocols (DNS, SSH, SNMP, NetFlow, etc.)
├── packets/         # Packet header formats (Ethernet, IPv4/v6, TCP/UDP, etc.)
└── reference/       # Quick-reference tables (IP ranges, ports, ICMP, MTU)
```

## Content Guidelines

**Scope:** Primary vendors are Cisco IOS-XE and FortiGate. Also include Equinix Fabric Cloud Router
(FCR) for multi-cloud and datacenter interconnect. Do not add other vendors (Juniper, Arista, etc.).

**Pairing Rules:**

- DSCP and QoS must be paired — do not add DSCP reference without accompanying QoS content
- LLDP and CDP should be documented together in the same section
- Equinix FCR guides should include both Cisco and FortiGate examples (separate guides per vendor)

**Markdown Requirements:**

- Every file must start with a top-level H1 heading (`# Title`)
- Line length: 100 characters max (no limit for code blocks or tables)
- Allowed inline HTML: `<br>`, `<details>`, `<summary>` (for collapsible sections)
- Duplicate heading names allowed only across different sections (e.g., multiple "Examples" headers
    in different docs)

**Architecture Diagrams:** Use Mermaid (supported via `pymdownx.superfences`) for flowcharts, sequence
diagrams, and architecture layouts.

## Markdown Formatting Standards

**Code Blocks:**

- Always close code blocks with exactly 3 backticks: ` ``` ` (never ` ```text ` or ` ```ios `)
- Opening backticks may have a language tag: ` ```ios `, ` ```fortios `, ` ```mermaid `, ` ```bash `
- Closing backticks must be bare: ` ``` ` — never include language identifiers
- Language tags: `ios` (Cisco IOS-XE), `fortios` (FortiOS), `bash` (shell), `text` (plaintext output)
- Each code block must have exactly one closing fence; never nest code blocks
- Blank line before code block opening (unless immediately after a heading)
- Blank line after code block closing (unless at end of section)

**Code Block Example — Correct:**

```ios
router bgp 65001
 address-family ipv4
  neighbor 192.0.2.1 activate
 exit-address-family
!
```

**Code Block Example — Wrong (closing fence has language tag):**

The following has an error that prevents rendering:

```text
router bgp 65001
 address-family ipv4
```ios
```

**Lists:**

- Ordered lists: use `1.`, `2.`, `3.` (auto-renumbering works automatically)
- Unordered lists: use `-` (hyphens only; no `*` or `+`)
- **Never** insert blank lines between consecutive list items — this breaks the list
- Blank line after a list is OK; required before next paragraph or heading
- List items spanning multiple lines: indent continuation with 2 spaces
- Nested lists: indent sub-items with 2 spaces, starting on new line

**List Example — Correct:**

```text
- Item 1
- Item 2
- Item 3

Next paragraph here.
```

**List Example — Wrong (blank lines break the list):**

```text
- Item 1

- Item 2
- Item 3
```

**Common Issues to Avoid:**

| Issue | Symptom | Fix |
| --- | --- | --- |
| Closing fence with language tag | Backticks appear in HTML | Replace ` ```ios `, ` ```text ` with ` ``` ` |
| Blank lines in list | List breaks into separate lists | Remove blank lines between items |
| Missing blank line before code block | Parser confusion | Add blank line before opening backticks |
| Indentation in code blocks | Content as inline code | Use 0-indent; flush left |

## Pre-Commit Workflow

Pre-commit hooks run automatically on `git commit`. They enforce:

1. **File Hygiene** (fastest): Remove trailing whitespace, fix EOF, normalize line endings, prevent
    large files
2. **Python Formatting** (Ruff): Format and lint any Python files (hooks.py)
3. **Markdown Linting**: Validate structure, line length, headings

Run `pre-commit run --all-files` to test all changes before committing.

## Navigation Structure

The site navigation is structured as 5 hierarchical categories (Home, Fundamentals, Cisco & FortiGate,
Cloud Architecture, Operations & Reference). Navigation is left-side collapsible with integrated TOC
on the right. Top-level categories expand/collapse; subsections are nested for a cleaner layout. The
navigation tree is defined in `mkdocs.yml` under the `nav:` section — keep it current when adding new
docs.

## Deployment

See `DEPLOYMENT.md` for Docker, Traefik, CI/CD (GitHub Actions / GitLab CI), and Watchtower container
auto-update setup.
