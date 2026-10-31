"""Check the Python and Rust sources."""

import functools
import sys

from project_checks import commands, python, rust


def lint(base: str = "HEAD", head: str = "") -> None:
    """Run Python checks and Rust Clippy concurrently.

    Defaults to HEAD versus local files. CI supplies --base and --head revisions.
    """
    sys.exit(
        commands.run_parallel(
            functools.partial(python.lint_python, base, head), rust.lint_rust
        )
    )
