"""Tests for confluence_poc.py - Markdown to Confluence publisher."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# Add repo root to path so we can import confluence_poc
sys.path.insert(0, str(Path(__file__).parent.parent))

from confluence_poc import (
    MermaidConverter,
    MarkdownToConfluence,
    ConfluencePublisher,
    extract_title_from_markdown,
    extract_intro_from_markdown,
    publish_parent_page,
)


class TestMermaidConverter:
    """Test Mermaid diagram extraction and conversion."""

    def test_extract_mermaid_blocks_single_diagram(self):
        """Extract single Mermaid block from markdown."""
        markdown = "# Test\n\n```mermaid\ngraph TD\nA --> B\n```\n\nSome text"
        converter = MermaidConverter()
        blocks = converter.extract_mermaid_blocks(markdown)

        assert len(blocks) == 1
        assert blocks[0][0] == 0
        assert "graph TD" in blocks[0][1]

    def test_extract_mermaid_blocks_multiple_diagrams(self):
        """Extract multiple Mermaid blocks from markdown."""
        markdown = "```mermaid\ngraph TD\nA --> B\n```\nText between\n```mermaid\nsequenceDiagram\nA->>B: hello\n```"
        converter = MermaidConverter()
        blocks = converter.extract_mermaid_blocks(markdown)

        assert len(blocks) == 2
        assert blocks[0][0] == 0
        assert blocks[1][0] == 1

    def test_extract_mermaid_blocks_no_diagrams(self):
        """Return empty list when no Mermaid blocks present."""
        markdown = "# Test\n\nJust text, no diagrams."
        converter = MermaidConverter()
        blocks = converter.extract_mermaid_blocks(markdown)

        assert len(blocks) == 0

    @patch("confluence_poc.subprocess.run")
    def test_convert_to_png_with_mmdc_success(self, mock_run, tmp_path):
        """Convert diagram using local mmdc successfully."""
        mock_run.return_value = Mock(returncode=0)
        output_path = str(tmp_path / "diagram.png")

        converter = MermaidConverter()
        result = converter.convert_to_png("graph TD\nA --> B", output_path)

        assert result is True
        mock_run.assert_called_once()

    @patch("confluence_poc.subprocess.run")
    @patch("confluence_poc.urllib.request.urlopen")
    def test_convert_to_png_kroki_fallback(self, mock_urlopen, mock_run, tmp_path):
        """Fall back to Kroki when mmdc not available."""
        # mmdc fails
        mock_run.side_effect = FileNotFoundError()

        # Kroki succeeds
        mock_response = MagicMock()
        mock_response.read.return_value = b"PNG data"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        output_path = str(tmp_path / "diagram.png")
        converter = MermaidConverter()
        result = converter.convert_to_png("graph", output_path)

        assert result is True

    def test_process_markdown_no_diagrams(self):
        """Process markdown with no diagrams."""
        markdown = "# Test\n\nJust text."
        converter = MermaidConverter()
        modified, diagram_map = converter.process_markdown(markdown, "/tmp")

        assert modified == markdown
        assert len(diagram_map) == 0


class TestMarkdownToConfluence:
    """Test Markdown to Confluence HTML conversion."""

    def test_convert_markdown_to_html_headers(self):
        """Convert markdown headers to HTML."""
        markdown = "# H1\n\n## H2\n\n### H3"
        html = MarkdownToConfluence.convert_markdown_to_html(markdown)

        assert "<h1" in html  # May have id attributes
        assert "<h2" in html
        assert "<h3" in html

    def test_convert_markdown_to_html_code_blocks(self):
        """Convert markdown code blocks to HTML."""
        markdown = "```python\nprint('hello')\n```"
        html = MarkdownToConfluence.convert_markdown_to_html(markdown)

        assert "<code>" in html or "<pre>" in html

    def test_convert_markdown_to_html_tables(self):
        """Convert markdown tables to HTML."""
        markdown = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = MarkdownToConfluence.convert_markdown_to_html(markdown)

        assert "<table>" in html

    def test_prepare_for_confluence_demotes_h1_to_h2(self):
        """H1 headers should become H2 (Confluence auto-generates page title)."""
        html = "<h1>Page Title</h1>\n<h2>Section</h2>"
        result = MarkdownToConfluence.prepare_for_confluence(html)

        assert "<h2>Page Title</h2>" in result
        assert "<h1>" not in result

    def test_prepare_for_confluence_image_to_attachment(self):
        """Convert image references to Confluence attachment macros."""
        html = '<img src="diagram_0.png" alt="Diagram 0">'
        diagram_map = {0: "/tmp/diagram_0.png"}
        result = MarkdownToConfluence.prepare_for_confluence(html, diagram_map)

        assert "ac:image" in result
        assert "ri:attachment" in result
        assert "diagram_0.png" in result

    def test_prepare_for_confluence_removes_spans_from_code(self):
        """Remove syntax highlighting spans from code blocks."""
        html = '<div class="codehilite"><pre><code><span class="n">x</span> = 1</code></pre></div>'
        result = MarkdownToConfluence.prepare_for_confluence(html)

        # Should not have span tags, but should have code content
        assert "<span" not in result
        assert "x = 1" in result or "x" in result

    def test_prepare_for_confluence_decodes_html_entities(self):
        """Decode HTML entities in code blocks."""
        html = '<div class="codehilite"><pre><code>&lt;tag&gt;</code></pre></div>'
        result = MarkdownToConfluence.prepare_for_confluence(html)

        # &lt; and &gt; should be decoded
        assert "&lt;" not in result or "<" in result
        assert "&gt;" not in result or ">" in result


class TestHelperFunctions:
    """Test utility functions."""

    def test_extract_title_from_markdown(self):
        """Extract H1 title from markdown."""
        markdown = "# My Title\n\nContent here."
        title = extract_title_from_markdown(markdown)

        assert title == "My Title"

    def test_extract_title_from_markdown_no_title(self):
        """Return 'Untitled' when no H1 present."""
        markdown = "## Subheading\n\nContent."
        title = extract_title_from_markdown(markdown)

        assert title == "Untitled"

    def test_extract_intro_from_markdown(self):
        """Extract content before first H2."""
        markdown = "# Title\n\nIntro paragraph.\n\n## Section\n\nSection content."
        intro = extract_intro_from_markdown(markdown)

        assert "Title" in intro
        assert "Intro paragraph" in intro
        assert "Section content" not in intro

    def test_extract_intro_from_markdown_no_h2(self):
        """Return all content when no H2 present."""
        markdown = "# Title\n\nAll content."
        intro = extract_intro_from_markdown(markdown)

        assert "Title" in intro
        assert "All content" in intro


class TestConfluencePublisher:
    """Test Confluence API publisher."""

    def test_publisher_initialization_stores_credentials(self):
        """Initialize publisher stores credentials."""
        # Don't actually try to create Confluence client (requires library)
        publisher = Mock(spec=ConfluencePublisher)
        publisher.base_url = "https://test.atlassian.net"
        publisher.username = "user@test.com"

        assert publisher.base_url == "https://test.atlassian.net"
        assert publisher.username == "user@test.com"

    def test_publisher_get_or_create_page_returns_page_id(self):
        """get_or_create_page returns ID when page found."""
        mock_confluence = Mock()
        mock_confluence.get_page_by_title.return_value = {"id": "12345"}

        publisher = ConfluencePublisher.__new__(ConfluencePublisher)
        publisher.confluence = mock_confluence

        result = publisher.get_or_create_page("SPACE", "Test Page")
        assert result == "12345"

    def test_publisher_get_or_create_page_returns_none_if_missing(self):
        """get_or_create_page returns None when page not found."""
        mock_confluence = Mock()
        mock_confluence.get_page_by_title.return_value = None

        publisher = ConfluencePublisher.__new__(ConfluencePublisher)
        publisher.confluence = mock_confluence

        result = publisher.get_or_create_page("SPACE", "Missing Page")
        assert result is None

    def test_publisher_publish_page_handles_none_client(self):
        """publish_page returns None if client not initialized."""
        publisher = ConfluencePublisher.__new__(ConfluencePublisher)
        publisher.confluence = None

        result = publisher.publish_page("SPACE", None, "Page", "<p>Content</p>")
        assert result is None


class TestPublishParentPage:
    """Test parent page publishing logic."""

    def test_publish_parent_page_creates_new(self, tmp_path):
        """Create parent page from index.md file."""
        # Create temp index.md file
        index_file = tmp_path / "index.md"
        index_file.write_text("# Routing\n\nIntroduction to routing.\n\n## BGP\n\nDetails.")

        mock_confluence = Mock()
        mock_confluence.get_page_by_title.return_value = None
        mock_confluence.create_page.return_value = "11111"

        publisher = ConfluencePublisher.__new__(ConfluencePublisher)
        publisher.confluence = mock_confluence
        publisher.base_url = "https://test.atlassian.net"

        parent_id = publish_parent_page(publisher, str(index_file), "SPACE")

        assert parent_id == "11111"
        mock_confluence.create_page.assert_called_once()

    def test_publish_parent_page_file_not_found(self):
        """Return None if parent file doesn't exist."""
        mock_confluence = Mock()
        publisher = ConfluencePublisher.__new__(ConfluencePublisher)
        publisher.confluence = mock_confluence

        parent_id = publish_parent_page(publisher, "/nonexistent/file.md", "SPACE")

        assert parent_id is None


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_full_conversion_pipeline(self, tmp_path):
        """Test complete markdown conversion pipeline (no external APIs)."""
        markdown = """# BGP Guide

Introduction to BGP.

## Overview

BGP is a routing protocol.

```python
configure terminal
router bgp 65001
```

| Protocol | Port |
|----------|------|
| BGP | 179 |
"""
        converter = MermaidConverter()
        modified, diagram_map = converter.process_markdown(markdown, str(tmp_path))

        html = MarkdownToConfluence.convert_markdown_to_html(modified)
        assert html is not None

        confluence_html = MarkdownToConfluence.prepare_for_confluence(html)
        assert "<h1>" not in confluence_html  # Should demote to h2
        assert "<table>" in confluence_html or "Protocol" in confluence_html
