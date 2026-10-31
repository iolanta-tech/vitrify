"""Format the Python and Rust sources."""

import sys

from project_checks import commands, python, rust


def fmt() -> None:
    """Format Python and Rust concurrently; exit nonzero if either changed files."""
    sys.exit(commands.run_parallel(python.format_python, rust.format_rust))
