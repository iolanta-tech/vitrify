"""Serve the documentation site."""

import sh


def serve() -> None:
    """Serve the Vitrify docs at http://localhost:6453."""
    sh.mkdocs.serve(
        "-a",
        "localhost:6453",
        _fg=True,
    )
