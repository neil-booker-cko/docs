def on_post_page(output, **_):
    """Remove leading whitespace and blank lines from rendered HTML output."""
    lines = (line.lstrip() for line in output.splitlines())
    return "\n".join(line for line in lines if line)
