# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Network Resilience Library** is a Zensical-based technical documentation site for network engineering
focusing on sub-second failover and hybrid-cloud connectivity. Content covers Cisco IOS-XE, Fortinet
FortiGate, cloud providers (AWS, Azure, GCP), and Equinix Fabric Cloud Router for multi-cloud
interconnection.

## Development Commands

```bash
# Start local preview server (rebuilds on file change)
uv run zensical serve

# Build static site (generates site/ directory)
uv run zensical build
```

**Utilities:**

```bash
# Run pre-commit hooks manually
pre-commit run --all-files

# Update dependencies
uv sync --all-groups
```

Site configuration is in `mkdocs.yml` (read natively by Zensical). See
[ZENSICAL_MIGRATION.md](ZENSICAL_MIGRATION.md) for background on the migration.

## Key Configuration Files

| File | Purpose |
| --- | --- |
| `mkdocs.yml` | Site structure, theme config, markdown extensions |
| `.markdownlint-cli2.yaml` | Markdown linting rules (100 char line length, code blocks/tables unlimited, H1 requirement, duplicate headings allowed in different sections) |
| `.pre-commit-config.yaml` | Automated checks: file hygiene, Python formatting (Ruff), markdown linting |
| `pyproject.toml` | Dependencies (zensical) and Python config |

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

## Theory Document Template & Categories

**Purpose:** Theory documents explain concepts, compare protocols, and provide design guidance.

**Categories (41 total):**

1. **Protocol Comparisons** (10 docs) — Compare two or more protocols/technologies head-to-head
   - Examples: eBGP vs iBGP, OSPF vs EIGRP, IPv4 vs IPv6, RADIUS vs TACACS+ vs LDAP

2. **Fundamentals** (8 docs) — Core concepts and foundational knowledge
   - Examples: Interface & Routing Fundamentals, IP Addressing Design, Switching Fundamentals

3. **Protocol & Technology Deep Dives** (13 docs) — Detailed explanation of a single protocol/feature
   - Examples: DMVPN, IPsec, QoS, BGP, OSPF, EIGRP, HSRP/VRRP/GLBP, Cloud Connectivity

4. **Architecture & Design** (7 docs) — Network topology and design patterns
   - Examples: DC Topologies, Cloud Network Design, Firewall Rule Processing, SD-WAN Design

5. **Security** (3 docs) — Security-focused protocols and practices
   - Examples: DHCP Security, IPsec, NAT

**Standard Template Structure:**

```text
# Title

[1-2 sentence intro: what this is and why it matters]

---

## At a Glance

[For comparisons: side-by-side table of key properties]
[For deep dives: quick reference of major sections]

---

## [Main Section 1]

[Explanation with diagrams where helpful]

### Subsection

[Details with examples]

---

## [Main Section 2]

[Follow same pattern]

---

## [Additional Sections as Needed]

[Typically: Use Cases, Best Practices, Examples, Troubleshooting]

---

## Notes / Gotchas

- **Key point 1:** Explanation
- **Key point 2:** Explanation

---

## See Also

- [Related doc](../path/doc.md)
- [Reference page](../reference/page.md)
```

**Key Guidelines:**

- Start with a compelling intro (why should someone read this?)
- Include "At a Glance" table or summary for quick scanning
- Use H2 for main sections, H3 for subsections (no deeper nesting)
- Include at least one Mermaid diagram for visual learners
- End with Notes/Gotchas section capturing non-obvious details
- Link to related docs and reference pages

## Markdown Formatting Standards

**Code Blocks:**

- Opening backticks may have a language tag: ` ```ios `, ` ```fortios `, ` ```mermaid `, ` ```bash `
- **Closing backticks must ALWAYS be bare: ` ``` `** — NEVER include language identifiers
  (` ```text ` or ` ```ios ` will break rendering)
- No blank line immediately after opening backticks — code starts on next line
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

- Ordered lists: use `1.` for all items (not `1.`, `2.`, `3.` — see "always 1" below)
- Unordered lists: use `-` (hyphens only; no `*` or `+`)
- **Never** insert blank lines between list items (ordered or unordered) — breaks the list
- Blank line after entire list is OK; required before next paragraph or heading
- List items spanning multiple lines: indent continuation with 2 spaces
- Nested lists: indent sub-items with 2 spaces, starting on new line

**Ordered List — Always Use `1.` (not manual numbering):**

Use this (markdown auto-increments during render):

```text
1. First item
1. Second item
1. Third item
```

Not this (manual numbering creates git diffs on reorder):

```text
1. First item
2. Second item
3. Third item
```

The "always 1" method keeps diffs clean when reordering or inserting items.

**List Example — Correct (unordered):**

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
| Blank line after opening backticks | Syntax highlighting breaks; garbled rendering | Remove blank line after ` ```bash `, start code on next line |
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
