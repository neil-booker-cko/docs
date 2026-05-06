#!/bin/bash
# Batch publish test: docs from folders with parent pages

set -e

echo "📚 Batch Publishing Test - 6 Documents"
echo "========================================"

# Routing docs with parent
echo ""
echo "📦 Routing Protocol Reference (parent + 3 children)"
uv run python confluence_poc.py docs/routing/bgp.md \
  --publish \
  --parent-file docs/routing/index.md

uv run python confluence_poc.py docs/routing/ospf.md \
  --publish \
  --parent-file docs/routing/index.md

uv run python confluence_poc.py docs/routing/eigrp.md \
  --publish \
  --parent-file docs/routing/index.md

# Reference docs with parent
echo ""
echo "📦 Reference Documentation (parent + 1 child)"
uv run python confluence_poc.py docs/reference/admin_distance.md \
  --publish \
  --parent-file docs/reference/index.md

# Application docs with parent
echo ""
echo "📦 Application Protocols (parent + 1 child)"
uv run python confluence_poc.py docs/application/dhcp.md \
  --publish \
  --parent-file docs/application/index.md

echo ""
echo "✅ Batch publish complete!"
echo ""
echo "📊 Summary:"
echo "  - 5 documents published"
echo "  - 3 parent pages (with children macro)"
echo "  - Multiple diagrams converted and embedded"
echo ""
echo "View in Confluence:"
echo "https://checkout.atlassian.net/wiki/spaces/~5fe0839e642089014165d146"
