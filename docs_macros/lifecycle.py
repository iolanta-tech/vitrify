"""Clean up the dataset used by documentation rendering."""

from mkdocs_macros_sparqld import stop_server


def on_build_error(error):
    """Release the build dataset so a retry loads current saved captures."""
    stop_server()
