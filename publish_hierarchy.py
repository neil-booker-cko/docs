#!/usr/bin/env python3
"""
Publish documentation to Confluence with automatic hierarchy creation.

Uses .confluence_hierarchy.json to define the structure.
Keeps docs folder clean—no index.md files needed.

This script:
1. Creates Documentation parent page in Confluence
2. Creates category parent pages under Documentation
3. Publishes individual docs under their category parents
4. Saves page IDs for future reference
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Optional
import subprocess
from dotenv import load_dotenv
from atlassian import Confluence

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Confluence settings
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_TOKEN = os.getenv("CONFLUENCE_TOKEN")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")

# Validate required env vars
if not all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_TOKEN, CONFLUENCE_SPACE_KEY]):
    logger.error("Missing required environment variables. Check .env file.")
    sys.exit(1)

# Load hierarchy config
with open(".confluence_hierarchy.json") as f:
    HIERARCHY_CONFIG = json.load(f)

# Initialize Confluence client
confluence = Confluence(url=CONFLUENCE_URL, username=CONFLUENCE_EMAIL, password=CONFLUENCE_TOKEN)


def publish_doc(file_path: str, parent_page_id: Optional[int] = None, title: Optional[str] = None) -> bool:
    """
    Publish a markdown file using confluence_poc.py.

    Args:
        file_path: Path to markdown file
        parent_page_id: Optional parent page ID
        title: Optional custom title (defaults to filename)

    Returns:
        True if successful, False otherwise
    """
    cmd = [
        "uv",
        "run",
        "python",
        "confluence_poc.py",
        file_path,
        "--publish",
    ]

    if parent_page_id:
        cmd.extend(["--parent-page-id", str(parent_page_id)])

    if title:
        cmd.extend(["--title", title])

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"✓ Published: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to publish {file_path}")
        logger.error(f"  {e.stderr}")
        return False


def get_page_id_by_title(title: str, space_key: str) -> Optional[int]:
    """
    Find a page by title in a space.

    Args:
        title: Page title
        space_key: Confluence space key

    Returns:
        Page ID if found, None otherwise
    """
    try:
        cql = f'title="{title}" AND space="{space_key}"'
        logger.debug(f"Querying CQL: {cql}")
        results = confluence.cql(cql)
        logger.debug(f"CQL results: {results}")

        if results.get("results") and len(results["results"]) > 0:
            page_id = results["results"][0]["content"]["id"]
            logger.debug(f"Found page ID: {page_id}")
            return int(page_id)

        logger.warning(f"No results found for '{title}' in space '{space_key}'")
        return None
    except Exception as e:
        logger.error(f"Error fetching page ID for '{title}': {e}")
        import traceback

        logger.debug(traceback.format_exc())
        return None


def create_documentation_page() -> Optional[int]:
    """
    Create the top-level Documentation page.

    Returns:
        Page ID if successful, None otherwise
    """
    logger.info("[1/3] Creating Documentation parent page...")

    doc_config = HIERARCHY_CONFIG["documentation"]
    title = doc_config["title"]
    description = doc_config.get("description", "")

    # Create a temporary markdown file for the Documentation page
    temp_file = "temp_documentation.md"
    with open(temp_file, "w") as f:
        f.write(f"# {title}\n\n{description}\n")

    try:
        publish_doc(temp_file, title=title)
        time.sleep(3)

        doc_page_id = get_page_id_by_title(title, CONFLUENCE_SPACE_KEY)
        if doc_page_id:
            logger.info(f"✓ {title} page ID: {doc_page_id}")
            return doc_page_id
        else:
            logger.error(f"Failed to get {title} page ID")
            return None
    finally:
        if Path(temp_file).exists():
            os.remove(temp_file)


def create_category_pages(doc_page_id: int) -> dict:
    """
    Create category parent pages under Documentation.

    Args:
        doc_page_id: Documentation page ID

    Returns:
        Dictionary mapping category folder names to page IDs
    """
    logger.info("\n[2/3] Creating category parent pages...")

    page_ids = {"documentation": doc_page_id}
    doc_config = HIERARCHY_CONFIG["documentation"]
    children = doc_config.get("children", {})

    for folder, display_name in children.items():
        docs_dir = Path(f"docs/{folder}")
        if not docs_dir.exists():
            logger.warning(f"Skipping {folder} - directory not found")
            continue

        logger.info(f"  Creating: {display_name}")

        # Create temporary markdown for category page
        temp_file = f"temp_{folder}.md"
        with open(temp_file, "w") as f:
            f.write(f"# {display_name}\n\n")

        try:
            publish_doc(temp_file, parent_page_id=doc_page_id, title=display_name)
            time.sleep(1)

            # Get category page ID
            category_page_id = get_page_id_by_title(display_name, CONFLUENCE_SPACE_KEY)
            if category_page_id:
                page_ids[folder] = category_page_id
                logger.info(f"  ✓ {display_name} page ID: {category_page_id}")
            else:
                logger.warning(f"  Could not get page ID for {display_name}")
        finally:
            if Path(temp_file).exists():
                os.remove(temp_file)

    return page_ids


def publish_category_docs(page_ids: dict) -> None:
    """
    Publish individual docs under their category parents.

    Args:
        page_ids: Dictionary mapping categories to page IDs
    """
    logger.info("\n[3/3] Publishing documentation files...")

    doc_config = HIERARCHY_CONFIG["documentation"]
    children = doc_config.get("children", {})

    for folder, display_name in children.items():
        if folder not in page_ids:
            logger.warning(f"Skipping {folder} - parent page not found")
            continue

        parent_id = page_ids[folder]
        docs_dir = Path(f"docs/{folder}")

        if not docs_dir.exists():
            continue

        md_files = sorted([f for f in docs_dir.glob("*.md") if f.suffix == ".md"])

        if md_files:
            logger.info(f"  {display_name}:")
            for md_file in md_files:
                logger.info(f"    - {md_file.name}")
                publish_doc(str(md_file), parent_page_id=parent_id)
                time.sleep(0.5)


def main():
    """Publish entire documentation hierarchy."""
    logger.info("Starting documentation hierarchy publishing...")
    logger.info(f"Using space: {CONFLUENCE_SPACE_KEY} at {CONFLUENCE_URL}\n")

    # Step 1: Create Documentation parent
    doc_page_id = create_documentation_page()
    if not doc_page_id:
        logger.error("Failed to create Documentation page. Aborting.")
        sys.exit(1)

    # Step 2: Create category parents
    page_ids = create_category_pages(doc_page_id)

    # Step 3: Publish individual docs
    publish_category_docs(page_ids)

    # Save page IDs for reference
    logger.info("\n[Summary] Page hierarchy created:")
    logger.info(f"Documentation (ID: {page_ids.get('documentation')})")

    doc_config = HIERARCHY_CONFIG["documentation"]
    children = doc_config.get("children", {})
    for folder, display_name in children.items():
        if folder in page_ids:
            logger.info(f"  └─ {display_name} (ID: {page_ids[folder]})")

    # Save IDs to file for future reference
    with open(".confluence_page_ids.json", "w") as f:
        json.dump(page_ids, f, indent=2)
    logger.info("\n✓ Page IDs saved to .confluence_page_ids.json")


if __name__ == "__main__":
    main()
