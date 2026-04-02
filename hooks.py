import re


def on_post_page(output, **kwargs):
    """Remove blank lines from rendered HTML output."""
    return re.sub(r"\n( *\n)+", "\n", output)
