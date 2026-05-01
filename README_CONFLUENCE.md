# Confluence Publishing

## Status: ✅ Fully Functional

Pipeline: Markdown → Mermaid diagrams → HTML → Confluence with folder
hierarchy and auto-generated navigation.

## Quick Start

### Single Document
```bash
uv run python confluence_poc.py docs/routing/bgp.md \
  --publish \
  --confluence-url "https://checkout.atlassian.net" \
  --confluence-email "neil.booker@checkout.com" \
  --confluence-token "YOUR_API_TOKEN" \
  --space-key "~5fe0839e642089014165d146"
```

### Just Convert (No Publish)
```bash
uv run python confluence_poc.py docs/theory/bgp_bfd_comparison.md \
  --output-dir ./output \
  --no-convert
```
Output: `./output/output.html` (ready for Confluence)

## Pipeline

```
Markdown (.md)
    ↓
Extract Mermaid diagrams (if present)
    ↓
Convert to PNG (local mmdc or Kroki API)
    ↓
Convert Markdown → HTML
    ↓
Confluence-safe HTML transformation
    ↓
Publish to Confluence (via REST API)
    ↓
Attach diagrams as images
```

## Credentials

### Option 1: Command-line Arguments
```bash
--confluence-url "https://checkout.atlassian.net"
--confluence-email "neil.booker@checkout.com"
--confluence-token "YOUR_API_TOKEN"
```

### Option 2: Environment Variables (Safer)
```bash
export CONFLUENCE_URL="https://checkout.atlassian.net"
export CONFLUENCE_EMAIL="neil.booker@checkout.com"
export CONFLUENCE_TOKEN="YOUR_API_TOKEN"

uv run python confluence_poc.py docs/routing/bgp.md --publish
```

## Your Space

- **URL:** https://checkout.atlassian.net/wiki/spaces/~5fe0839e642089014165d146
- **Space Key:** `~5fe0839e642089014165d146`
- **Name:** Neil Charles Booker (personal space)

## Features

✅ Markdown → HTML conversion (tables, code, headers, links)
✅ Mermaid diagram extraction and PNG conversion (mmdc + Kroki fallback)
✅ Diagram embedding with proper sizing (600px width)
✅ Folder hierarchy mirroring (docs/category/ → Confluence parent pages)
✅ Parent pages from index.md with auto-generated children macro
✅ Page creation and updates
✅ Confluence API authentication and publishing

## Folder Hierarchy & Navigation

### Auto-generated Parent Pages

Use `--parent-file` to publish an `index.md` as the parent page:

```bash
uv run python confluence_poc.py docs/routing/bgp.md \
  --publish \
  --parent-file docs/routing/index.md
```

This:
- Publishes `index.md` intro as the parent page
- Publishes `bgp.md` as a child under it
- Adds auto-generated "Child pages" list using Confluence's children macro

### Structure Example

```text
docs/routing/
├── index.md           ← Publish with --parent-file (becomes parent page)
├── bgp.md             ← Child page under "Routing"
├── ospf.md            ← Child page under "Routing"
└── eigrp.md           ← Child page under "Routing"
```

Results in Confluence:

- **Routing** (parent page from index.md)
  - BGP
  - OSPF
  - EIGRP

## Diagram Support

Install mermaid-cli for automatic diagram conversion:

```bash
npm install -g @mermaid-js/mermaid-cli
```

Diagrams auto-convert to PNG (1200px, 2x scale) and attach to pages.

### To Publish Multiple Docs
Create a batch script:
```bash
for file in docs/theory/*.md; do
  uv run python confluence_poc.py "$file" \
    --publish \
    --confluence-url "https://checkout.atlassian.net" \
    --confluence-email "neil.booker@checkout.com" \
    --confluence-token "$CONFLUENCE_TOKEN" \
    --space-key "~5fe0839e642089014165d146"
done
```

### To Set Up CI/CD
Add to GitHub Actions or GitLab CI:
```yaml
- name: Publish to Confluence
  env:
    CONFLUENCE_URL: ${{ secrets.CONFLUENCE_URL }}
    CONFLUENCE_EMAIL: ${{ secrets.CONFLUENCE_EMAIL }}
    CONFLUENCE_TOKEN: ${{ secrets.CONFLUENCE_TOKEN }}
  run: |
    uv run python confluence_poc.py docs/routing/bgp.md --publish
```

## Script Options

```bash
uv run python confluence_poc.py <markdown_file> [options]

Options:
  --output-dir PATH        Output directory for HTML/diagrams
  --no-convert             Skip Mermaid diagram conversion
  --publish                Publish to Confluence
  --confluence-url URL     Confluence base URL
  --confluence-email EMAIL Email for API auth
  --confluence-token TOK   API token for auth
  --space-key KEY          Confluence space key
  --parent-file FILE       Publish index.md as parent (e.g.,
                           docs/routing/index.md)
  --parent-page-id ID      Parent page ID (overrides auto-detect)
```

## Troubleshooting

### "Permission denied" error
- Ensure the API token is valid (check https://id.atlassian.com/manage-profile/security/api-tokens)
- Ensure you have write access to the space
- Try publishing to your personal space first (low barrier to test)

### Diagrams show as empty code blocks
- Install mermaid-cli: `npm install -g @mermaid-js/mermaid-cli`
- Re-run with diagram conversion enabled (don't use `--no-convert`)

### Markdown not rendering correctly
- Check `.markdownlint-cli2.yaml` for supported syntax
- Ensure no blank lines inside lists (breaks Markdown parsing)
- Use `<!-- -->` comments, not `//` for hidden notes

## Files

- **confluence_poc.py** — Main conversion & publishing script (500+ lines)
- **CONFLUENCE_INTEGRATION.md** — Detailed implementation guide
- **README_CONFLUENCE.md** — This file
- **pyproject.toml** — Updated with atlassian-python-api, markdown dependencies

## See Also

- [Confluence REST API Docs](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [atlassian-python-api Library](https://github.com/atlassian-api/atlassian-python-api)
- [Mermaid Diagram Syntax](https://mermaid.js.org/)
