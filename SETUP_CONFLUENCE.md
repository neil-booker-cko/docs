# Confluence Publishing Setup Guide

Complete instructions for publishing your documentation from this repo to Confluence.

## Prerequisites

You'll need:

- **Python 3.12+** (for the publishing script)
- **Node.js LTS** (for Mermaid diagram conversion)
- **uv** (Python package manager — already used by this project)
- **Git** (to clone/work with the repo)

---

## Step 1: Install Node.js

Install **Node.js 20.x LTS or newer** (latest LTS is 22.x as of 2026).

### macOS / Linux (Recommended: NVM)

**Use NVM (Node Version Manager)** — avoids old apt/brew versions:

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Reload your shell
source ~/.bashrc
# or if using zsh:
source ~/.zshrc

# Install latest LTS
nvm install --lts

# Use it
nvm use --lts
```

### macOS Alternative: Homebrew

```bash
brew install node
```

### Ubuntu/Debian Alternative: NodeSource PPA

⚠️ **Note:** `apt` has very old Node.js versions. Use nvm instead, or:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Windows (Recommended: WSL2 + Ubuntu)

**Use WSL (Windows Subsystem for Linux)** — much better for development:

**1. Install WSL2 with Ubuntu:**

```powershell
# Run in PowerShell as Administrator
wsl --install -d Ubuntu
```

See [WSL docs](https://learn.microsoft.com/en-us/windows/wsl/install) for detailed instructions.

**2. Then follow the Linux/macOS instructions above** (use nvm in Ubuntu):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install --lts
```

**3. Install Chromium dependencies** (required for mmdc on WSL2):

```bash
sudo apt-get update
sudo apt-get install -y \
  ca-certificates fonts-liberation libatk-bridge2.0-0t64 \
  libatk1.0-0t64 libc6 libcairo2 libcups2t64 libdbus-1-3 \
  libexpat1 libfontconfig1 libgbm1 libgcc-s1 libglib2.0-0t64 \
  libgtk-3-0t64 libnspr4 libnss3 libpango-1.0-0 \
  libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 \
  libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 \
  libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 \
  libxtst6 wget xdg-utils
```

These are dependencies for Puppeteer/Chromium (used internally by mmdc for diagram rendering).

### Windows Native (Alternative)

If you prefer not to use WSL, download from [nodejs.org](https://nodejs.org/).
Choose **LTS version** (currently 22.x) and run the installer.

**Verify installation:**

```bash
node --version   # Should be v20.x or newer (v22.x recommended)
npm --version    # Should be v10.x or newer
```

---

## Step 2: Install Mermaid CLI

```bash
npm install -g @mermaid-js/mermaid-cli
```

**Verify it works:**

```bash
mmdc --version
```

You should see a version number like `10.x.x` or newer.

---

## Step 3: Set Up Confluence Credentials

### Create `.env` file

In the repo root, create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

### Edit `.env` with your credentials

```bash
nano .env  # or your favorite editor
```

Fill in:

```bash
CONFLUENCE_URL=https://checkout.atlassian.net
CONFLUENCE_EMAIL=neil.booker@checkout.com
CONFLUENCE_TOKEN=your-api-token-here
CONFLUENCE_SPACE_KEY=~5fe0839e642089014165d146
```

**How to get your API token:**

1. Go to <https://id.atlassian.com/manage-profile/security/api-tokens>
1. Click **Create API token**
1. Give it a name like "Confluence Publisher"
1. Copy the token and paste it into `.env`

### Protect your credentials

**Important:** Never commit `.env` to git. It's already in `.gitignore`, but verify:

```bash
cat .gitignore | grep "\.env"
```

Should show:

```text
.env
```

---

## Step 4: Install Python Dependencies

From the repo root:

```bash
uv sync --all-groups
```

This installs:

- `playwright` — For diagram rendering (fallback)
- `markdown` — For Markdown → HTML conversion
- `atlassian-python-api` — For Confluence REST API
- `python-dotenv` — For `.env` file loading

---

## Step 5: Test the Setup

### Test conversion only (no publish)

```bash
uv run python confluence_poc.py docs/routing/bgp.md --output-dir ./test_output --no-convert
```

This generates `test_output/output.html` so you can preview the HTML without publishing.

### Test with diagram conversion

```bash
uv run python confluence_poc.py docs/theory/bgp_bfd_comparison.md --output-dir ./test_output
```

This will convert Mermaid diagrams to PNG in `test_output/diagram_*.png`.

**Expected output:**

```text
✓ Converted diagram 0 → diagram_0.png
✓ Converted diagram 1 → diagram_1.png
✓ Markdown converted to HTML
✓ HTML prepared for Confluence
```

### Publish a test page

```bash
uv run python confluence_poc.py docs/reference/admin_distance.md --publish
```

Check your Confluence space: <https://checkout.atlassian.net/wiki/spaces/~5fe0839e642089014165d146/>

The page should appear with:

- ✅ Proper formatting
- ✅ Code blocks with line breaks
- ✅ Tables and headers
- ✅ Mermaid diagrams as PNG images

---

## Common Commands

### Publish a single document

```bash
uv run python confluence_poc.py docs/routing/bgp.md --publish
```

### Publish multiple docs (batch)

```bash
for file in docs/theory/*.md; do
  echo "Publishing: $file"
  uv run python confluence_poc.py "$file" --publish
done
```

### Publish without diagram conversion (faster)

```bash
uv run python confluence_poc.py docs/routing/bgp.md --publish --no-convert
```

### Just convert (preview HTML, don't publish)

```bash
uv run python confluence_poc.py docs/routing/bgp.md --output-dir ./preview
cat preview/output.html
```

### Override the space

```bash
uv run python confluence_poc.py docs/routing/bgp.md --publish --space-key NETDOCS
```

---

## Diagram Conversion Methods (Priority)

The script tries these in order:

### 1. Local mmdc (Fastest)

Requires `npm install -g @mermaid-js/mermaid-cli`

**Pros:** Fast, reliable, offline
**Cons:** Requires Node.js

### 2. Playwright (Pure Python)

Built-in, no extra install

**Pros:** No Node.js needed, pure Python
**Cons:** Requires internet to download Mermaid.js from CDN

### 3. Kroki Online API (Fallback)

Free online service

**Pros:** No local installation
**Cons:** May be blocked by corporate proxy, requires internet

---

## Troubleshooting

### `mmdc: command not found`

**Problem:** mermaid-cli not installed or not in PATH

**Solution:**

```bash
npm install -g @mermaid-js/mermaid-cli
# Verify:
mmdc --version
```

### `ERROR: Missing Confluence credentials`

**Problem:** `.env` file not found or incomplete

**Solution:**

```bash
# Verify .env exists and has all fields:
cat .env

# Should show:
CONFLUENCE_URL=https://checkout.atlassian.net
CONFLUENCE_EMAIL=neil.booker@checkout.com
CONFLUENCE_TOKEN=xxx
CONFLUENCE_SPACE_KEY=~5fe0839e642089014165d146
```

### `A page with this title already exists`

**Problem:** Page already published, script is trying to create instead of update

**Solution:** The script auto-detects existing pages and updates them. If it happens,
re-run the command—it will update instead of creating.

### Diagrams show as code blocks instead of PNG

**Problem:** Diagram conversion failed (network restricted or mmdc not installed)

**Solutions:**

1. Ensure Node.js is installed: `node --version`
2. Ensure mmdc is installed: `mmdc --version`
3. Check internet access (Playwright needs to download Mermaid.js)
4. Run with `--no-convert` flag if you just want to publish without diagrams

### `playwright install chromium` errors

**Problem:** Playwright browser download failed

**Solution:**

```bash
playwright install chromium
# Or reinstall:
pip install --upgrade playwright
playwright install chromium
```

---

## Workflow: Publish All Docs

Once everything is set up:

```bash
#!/bin/bash
# publish_all.sh

set -e  # Exit on error

echo "📚 Publishing all documentation to Confluence..."

# Load credentials
source .env

# Publish theory docs
for file in docs/theory/*.md; do
  title=$(basename "$file")
  echo "📄 Publishing: $title"
  uv run python confluence_poc.py "$file" --publish
done

# Publish routing docs
for file in docs/routing/*.md; do
  title=$(basename "$file")
  echo "📄 Publishing: $title"
  uv run python confluence_poc.py "$file" --publish
done

# Publish reference docs
for file in docs/reference/*.md; do
  title=$(basename "$file")
  echo "📄 Publishing: $title"
  uv run python confluence_poc.py "$file" --publish
done

echo "✅ All docs published!"
```

Save as `publish_all.sh` and run:

```bash
chmod +x publish_all.sh
./publish_all.sh
```

---

## CI/CD: Auto-Publish on Git Push

To auto-publish when you push to `main`:

### GitHub Actions (`.github/workflows/publish.yml`)

```yaml
name: Publish to Confluence
on:
  push:
    branches: [main]
    paths: ['docs/**']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
      - run: npm install -g @mermaid-js/mermaid-cli

      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install uv && uv sync --all-groups

      - name: Publish to Confluence
        env:
          CONFLUENCE_URL: ${{ secrets.CONFLUENCE_URL }}
          CONFLUENCE_EMAIL: ${{ secrets.CONFLUENCE_EMAIL }}
          CONFLUENCE_TOKEN: ${{ secrets.CONFLUENCE_TOKEN }}
          CONFLUENCE_SPACE_KEY: ${{ secrets.CONFLUENCE_SPACE_KEY }}
        run: |
          for file in docs/**/*.md; do
            uv run python confluence_poc.py "$file" --publish
          done
```

**To set up secrets:**

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `CONFLUENCE_URL`
   - `CONFLUENCE_EMAIL`
   - `CONFLUENCE_TOKEN`
   - `CONFLUENCE_SPACE_KEY`

---

## Tips & Best Practices

### 1. Test before committing

Always test locally before pushing:

```bash
uv run python confluence_poc.py docs/routing/bgp.md --publish --no-convert
```

### 2. Use meaningful commit messages

```bash
git commit -m "docs: update BGP guide with BFD section"
```

### 3. Keep `.env` local only

Never commit credentials:

```bash
# Verify .env is ignored:
git check-ignore .env  # Should print: .env
```

### 4. Monitor Confluence

After publishing, check the page in Confluence to ensure:

- Code blocks have proper formatting
- Tables render correctly
- Diagrams display as images (not code blocks)
- Links work

### 5. Regenerate API token periodically

For security, rotate your Confluence API token every 90 days:

1. Generate new token at <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Update `.env` with the new token
3. Delete the old token

---

## Quick Reference

| Task | Command |
| --- | --- |
| **Install mmdc** | `npm install -g @mermaid-js/mermaid-cli` |
| **Set up .env** | `cp .env.example .env && nano .env` |
| **Install deps** | `uv sync --all-groups` |
| **Test conversion** | `uv run python confluence_poc.py docs/file.md --output-dir ./out` |
| **Publish one page** | `uv run python confluence_poc.py docs/file.md --publish` |
| **Publish all** | `for f in docs/**/*.md; do uv run python confluence_poc.py "$f" --publish; done` |
| **Skip diagrams** | `uv run python confluence_poc.py docs/file.md --publish --no-convert` |

---

## Support

For issues with the publishing script, check:

- [confluence_poc.py](confluence_poc.py) — Main script
- [README_CONFLUENCE.md](README_CONFLUENCE.md) — Quick start guide
- [CONFLUENCE_INTEGRATION.md](CONFLUENCE_INTEGRATION.md) — Technical details

For Confluence API issues, see:

- [Atlassian Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v2/intro/)
- [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api)
