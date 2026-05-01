#!/usr/bin/env python3
"""
POC: Markdown → Confluence publisher with Mermaid diagram conversion.

Requirements:
- mermaid-cli (npm install -g @mermaid-js/mermaid-cli) — OPTIONAL, uses online API as fallback
- markdown (pip install markdown) — for Markdown → HTML conversion
- atlassian-python-api (pip install atlassian-python-api) — for Confluence publishing

Usage:
    python confluence_poc.py <markdown_file> [--output-dir ./output]
"""

import argparse
import os
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    load_dotenv()  # Load .env file
except ImportError:
    pass  # If python-dotenv not installed, just use env vars


class MermaidConverter:
    """Extract and convert Mermaid diagrams from Markdown to PNG."""

    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.diagrams = []

    def extract_mermaid_blocks(self, markdown_content: str) -> list[tuple[int, str]]:
        """
        Extract Mermaid diagram blocks from Markdown.

        Returns:
            List of (block_number, diagram_content) tuples
        """
        pattern = r"```mermaid\n(.*?)\n```"
        matches = list(re.finditer(pattern, markdown_content, re.DOTALL))
        return [(i, m.group(1)) for i, m in enumerate(matches)]

    def convert_to_png(self, diagram_content: str, output_path: str) -> bool:
        """
        Convert Mermaid diagram to PNG.
        Tries (in order):
        1. Local mmdc (npm install -g @mermaid-js/mermaid-cli)
        2. Playwright (pure Python, no dependencies)
        3. Kroki online API (fallback, may be blocked by corporate proxy)
        """
        # Try local mermaid-cli first
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
                f.write(diagram_content)
                temp_mmd = f.name

            cmd = ["mmdc", "-i", temp_mmd, "-o", output_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            os.unlink(temp_mmd)

            if result.returncode == 0:
                return True

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Try Playwright (pure Python, works offline)
        try:
            print("   → Using Playwright for diagram conversion...")
            return self._convert_with_playwright(diagram_content, output_path)
        except Exception as e:
            print(f"   → Playwright failed: {e}")

        # Fallback to Kroki online API
        try:
            print("   → Using Kroki online API for diagram conversion...")
            kroki_url = "https://kroki.io/mermaid/png"

            diagram_bytes = diagram_content.encode("utf-8")
            req = urllib.request.Request(
                kroki_url,
                data=diagram_bytes,
                headers={"Content-Type": "text/plain"},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                png_data = response.read()
                with open(output_path, "wb") as f:
                    f.write(png_data)
            return True

        except Exception as e:
            print(f"ERROR converting diagram: {e}")
            return False

    def _convert_with_playwright(self, diagram_content: str, output_path: str) -> bool:
        """Render Mermaid diagram using Playwright headless browser."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return False

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <style>
                body {{ margin: 0; padding: 20px; background: white; }}
                .mermaid {{ display: flex; justify-content: center; }}
            </style>
        </head>
        <body>
            <div class="mermaid">
{diagram_content}
            </div>
            <script>
                mermaid.initialize({{ startOnLoad: true }});
                mermaid.contentLoaded();
            </script>
        </body>
        </html>
        """

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()

                # Set content and wait for Mermaid to render
                page.set_content(html_template)
                page.wait_for_load_state("networkidle")

                # Take screenshot
                page.screenshot(path=output_path)
                browser.close()

            return True

        except Exception as e:
            print(f"Playwright error: {e}")
            return False

    def process_markdown(self, markdown_content: str, output_dir: str) -> tuple[str, dict]:
        """
        Extract Mermaid diagrams and convert to PNG.

        Returns:
            (modified_markdown, diagram_map)
            - modified_markdown: markdown with ![]() image refs instead of mermaid blocks
            - diagram_map: {original_diagram_id: png_file_path}
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        diagrams = self.extract_mermaid_blocks(markdown_content)
        diagram_map = {}
        modified_content = markdown_content

        for block_num, diagram_content in diagrams:
            # Generate PNG
            png_name = f"diagram_{block_num}.png"
            png_path = os.path.join(output_dir, png_name)

            if self.convert_to_png(diagram_content, png_path):
                diagram_map[block_num] = png_path
                print(f"✓ Converted diagram {block_num} → {png_name}")

                # Replace mermaid block with image reference
                mermaid_block = f"```mermaid\n{diagram_content}\n```"
                image_ref = f"![Diagram {block_num}]({png_name})"
                modified_content = modified_content.replace(mermaid_block, image_ref, 1)
            else:
                print(f"✗ Failed to convert diagram {block_num}")

        return modified_content, diagram_map


class MarkdownToConfluence:
    """Convert Markdown to Confluence format (XHTML)."""

    @staticmethod
    def convert_markdown_to_html(markdown_content: str) -> Optional[str]:
        """
        Convert Markdown to HTML using Python markdown library.

        Requires: pip install markdown
        """
        try:
            import markdown

            extensions = [
                "tables",  # For | table | syntax
                "fenced_code",  # For ```code``` blocks
                "codehilite",  # For syntax highlighting
                "toc",  # For table of contents
            ]

            html = markdown.markdown(markdown_content, extensions=extensions)
            return html

        except ImportError:
            print("WARNING: markdown not installed. Falling back to basic conversion...")
            return MarkdownToConfluence._simple_html_fallback(markdown_content)

    @staticmethod
    def _simple_html_fallback(markdown_content: str) -> str:
        """Simple HTML conversion without markdown library."""
        html = markdown_content

        # H1-H6 headers
        for i in range(1, 7):
            pattern = f"^{'#' * i} (.+)$"
            replacement = f"<h{i}>\\1</h{i}>"
            html = re.sub(pattern, replacement, html, flags=re.MULTILINE)

        # Bold and italic
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # Code blocks
        html = re.sub(
            r"```(\w+)?\n(.*?)\n```",
            r'<pre><code class="language-\1">\2</code></pre>',
            html,
            flags=re.DOTALL,
        )

        # Inline code
        html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)

        # Links
        html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', html)

        # Line breaks to paragraphs
        html = re.sub(r"\n\n+", "</p><p>", html)
        html = f"<p>{html}</p>"

        return html

    @staticmethod
    def prepare_for_confluence(html_content: str) -> str:
        """
        Prepare HTML for Confluence publishing.

        - Convert <h1> to <h2> (Confluence pages have auto-generated h1)
        - Strip syntax highlighting spans from code blocks for Confluence compatibility
        - Preserve code blocks with proper whitespace
        """
        # Demote h1 → h2 (Confluence auto-generates page title)
        content = re.sub(r"<h1>([^<]+)</h1>", r"<h2>\1</h2>", html_content)

        # Strip codehilite spans but preserve code content and structure
        # Replace <div class="codehilite"><pre><span></span><code>...<span class="w"> </span>..
        # with simple <pre><code>...\n...</code></pre>
        def clean_code_block(match):
            block = match.group(1)
            # Remove all <span> tags but keep content
            cleaned = re.sub(r"<span[^>]*>", "", block)
            cleaned = re.sub(r"</span>", "", cleaned)
            # Decode HTML entities in code
            cleaned = cleaned.replace("&lt;", "<").replace("&gt;", ">")
            cleaned = cleaned.replace("&quot;", '"').replace("&#x27;", "'")
            cleaned = cleaned.replace("&amp;", "&")
            return f"<pre><code>{cleaned}</code></pre>"

        content = re.sub(
            r'<div class="codehilite"><pre>.*?<code>(.*?)</code></pre></div>',
            clean_code_block,
            content,
            flags=re.DOTALL,
        )

        return content


class ConfluencePublisher:
    """Publish content to Confluence via REST API."""

    def __init__(self, base_url: str, username: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.api_token = api_token

        try:
            from atlassian import Confluence

            self.confluence = Confluence(
                url=self.base_url,
                username=username,
                password=api_token,  # API token goes in password field
            )
        except ImportError:
            print("ERROR: atlassian-python-api not installed")
            print("Install with: pip install atlassian-python-api")
            self.confluence = None

    def get_or_create_page(self, space_key: str, title: str, parent_page_id: Optional[int] = None) -> Optional[int]:
        """
        Find existing page or return None (for create).

        Returns:
            Page ID if found, None if doesn't exist
        """
        try:
            # Search for existing page by title
            cql = f'type = page AND title ~ "{title}" AND space = "{space_key}"'
            results = self.confluence.cql(cql)

            if results["results"]:
                page_id = results["results"][0]["id"]
                print(f"✓ Found existing page: ID {page_id}")
                return page_id

            return None
        except Exception as e:
            print(f"Warning: Could not search for existing page: {e}")
            return None

    def publish_page(
        self,
        space_key: str,
        parent_page_id: Optional[int],
        title: str,
        html_content: str,
        attachments: Optional[dict[int, str]] = None,
    ) -> Optional[int]:
        """
        Publish or update page in Confluence.

        Args:
            space_key: Confluence space key (e.g., 'DOC')
            parent_page_id: Parent page ID for hierarchy (optional)
            title: Page title
            html_content: XHTML body content
            attachments: Dict of {diagram_id: file_path}

        Returns:
            Page ID if successful, None otherwise
        """
        if not self.confluence:
            print("ERROR: Confluence client not initialized")
            return None

        try:
            print("\n📤 Publishing to Confluence...")
            print(f"   Space: {space_key}")
            print(f"   Title: {title}")
            print(f"   Content: {len(html_content)} chars")

            # Check if page already exists
            existing_id = self.get_or_create_page(space_key, title, parent_page_id)

            if existing_id:
                # Update existing page
                print(f"   Updating page {existing_id}...")
                self.confluence.update_page(
                    page_id=existing_id,
                    title=title,
                    body=html_content,
                    minor_edit=False,
                )
                page_id = existing_id
            else:
                # Create new page
                print("   Creating new page...")
                page_id = self.confluence.create_page(
                    space=space_key,
                    title=title,
                    body=html_content,
                    parent_id=parent_page_id,
                )

            print(f"✓ Page published: {self.base_url}/wiki/spaces/{space_key}/pages/{page_id}")

            # Attach diagrams if provided
            if attachments:
                self._attach_diagrams(page_id, attachments)

            return page_id

        except Exception as e:
            print(f"ERROR publishing page: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _attach_diagrams(self, page_id: int, attachments: dict[int, str]):
        """Attach PNG diagrams to page."""
        try:
            for diagram_id, file_path in attachments.items():
                if not os.path.exists(file_path):
                    print(f"   Warning: Diagram file not found: {file_path}")
                    continue

                print(f"   Attaching: {os.path.basename(file_path)}...")
                self.confluence.attach_file(
                    filename=file_path,
                    page_id=page_id,
                    title=f"Diagram {diagram_id}",
                )
                print(f"   ✓ Attached {os.path.basename(file_path)}")

        except Exception as e:
            print(f"   Warning: Could not attach diagrams: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown with Mermaid diagrams → Confluence")
    parser.add_argument("markdown_file", help="Path to markdown file")
    parser.add_argument(
        "--output-dir",
        default="./confluence_output",
        help="Output directory for PNG diagrams",
    )
    parser.add_argument("--no-convert", action="store_true", help="Skip Mermaid conversion")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish to Confluence (requires --confluence-* args)",
    )
    parser.add_argument(
        "--confluence-url",
        default=os.getenv("CONFLUENCE_URL"),
        help="Confluence base URL (or CONFLUENCE_URL env var)",
    )
    parser.add_argument(
        "--confluence-email",
        default=os.getenv("CONFLUENCE_EMAIL"),
        help="Confluence email (or CONFLUENCE_EMAIL env var)",
    )
    parser.add_argument(
        "--confluence-token",
        default=os.getenv("CONFLUENCE_TOKEN"),
        help="Confluence API token (or CONFLUENCE_TOKEN env var)",
    )
    parser.add_argument(
        "--space-key",
        default=os.getenv("CONFLUENCE_SPACE_KEY", "~neil_booker"),
        help="Confluence space key (or set CONFLUENCE_SPACE_KEY)",
    )
    parser.add_argument(
        "--parent-page-id",
        type=int,
        help="Parent page ID for hierarchy (optional)",
    )
    args = parser.parse_args()

    # Read markdown file
    with open(args.markdown_file, "r") as f:
        markdown_content = f.read()

    print(f"📄 Processing: {args.markdown_file}")
    print(f"   Size: {len(markdown_content)} chars\n")

    # Extract title from H1
    title_match = re.match(r"# (.+)\n", markdown_content)
    title = title_match.group(1) if title_match else "Untitled"

    # Step 1: Convert Mermaid diagrams to PNG
    diagram_map = {}
    if not args.no_convert:
        print("🔄 Converting Mermaid diagrams...\n")
        converter = MermaidConverter()
        markdown_content, diagram_map = converter.process_markdown(markdown_content, args.output_dir)

        if diagram_map:
            print(f"\n✓ Generated {len(diagram_map)} PNG(s)")
            for idx, path in diagram_map.items():
                print(f"   Diagram {idx}: {path}")

    # Step 2: Convert Markdown to HTML
    print("\n🔄 Converting Markdown → HTML...\n")
    html_content = MarkdownToConfluence.convert_markdown_to_html(markdown_content)

    if html_content:
        print("✓ Markdown converted to HTML")
        print(f"   HTML size: {len(html_content)} chars")

        # Step 3: Prepare for Confluence
        print("\n🔄 Preparing for Confluence...\n")
        confluence_html = MarkdownToConfluence.prepare_for_confluence(html_content)
        print("✓ HTML prepared for Confluence")

        # Write output files
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        html_file = os.path.join(args.output_dir, "output.html")
        with open(html_file, "w") as f:
            f.write(confluence_html)
        print(f"   Saved to: {html_file}")

        # Step 4: Publish to Confluence (if enabled)
        if args.publish:
            if not all([args.confluence_url, args.confluence_email, args.confluence_token]):
                print("\n❌ ERROR: Missing Confluence credentials")
                print("Provide via:")
                print("  --confluence-url <url>")
                print("  --confluence-email <email>")
                print("  --confluence-token <token>")
                print("\nOr set environment variables:")
                print("  CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_TOKEN")
                return 1

            print("\n🔄 Publishing to Confluence...\n")
            publisher = ConfluencePublisher(
                base_url=args.confluence_url,
                username=args.confluence_email,
                api_token=args.confluence_token,
            )

            page_id = publisher.publish_page(
                space_key=args.space_key,
                parent_page_id=args.parent_page_id,
                title=title,
                html_content=confluence_html,
                attachments=diagram_map if diagram_map else None,
            )

            if page_id:
                print("\n✅ Success! Published to Confluence")
            else:
                print("\n❌ Failed to publish to Confluence")
                return 1
        else:
            print("\n✓ Conversion complete!")
            print("\nTo publish to Confluence, add: --publish \\")
            print("  --confluence-url https://checkout.atlassian.net \\")
            print("  --confluence-email neil.booker@checkout.com \\")
            print("  --confluence-token <your-token>")

        print("\nOutput files:")
        print(f"  HTML: {html_file}")
        if diagram_map:
            for idx, path in diagram_map.items():
                print(f"  Diagram {idx}: {path}")
    else:
        print("✗ Failed to convert Markdown")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
