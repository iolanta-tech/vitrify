"""Project tasks for Vitrify. Run with `j <task>` (see https://jeeves.sh)."""

import sys
import functools
from pathlib import Path

import sh

import example_runner
from project_checks import commands, python, rust

RETRIEVAL_SCRIPT = "retrieve.sh"
PROJECT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = PROJECT_DIR / "docs" / "examples"

EXAMPLES = (
    ("female-persons", RETRIEVAL_SCRIPT, "."),
    ("top-metaclasses", RETRIEVAL_SCRIPT, "."),
    ("metaclasses-of-metaclasses", RETRIEVAL_SCRIPT, "."),
    ("fourth-order-classes", RETRIEVAL_SCRIPT, "."),
    ("select-turtle", RETRIEVAL_SCRIPT, "."),
    ("time-bounded-subclasses", RETRIEVAL_SCRIPT, "."),
    ("basic-example", "input/retrieve.sh", "eu-capitals"),
)


def examples() -> None:
    """Append one retrieval per endpoint for every example and validate each crate."""
    if example_runner.run_examples(EXAMPLES, EXAMPLES_DIR):
        sys.exit(1)


def serve() -> None:
    """Serve the Vitrify docs at http://localhost:6453."""
    sh.mkdocs.serve(
        "-a",
        "localhost:6453",
        _fg=True,
    )


def fmt() -> None:
    """Format Python and Rust concurrently; exit nonzero if either changed files."""
    sys.exit(commands.run_parallel(python.format_python, rust.format_rust))


def lint(base: str = "HEAD", head: str = "") -> None:
    """Run Python checks and Rust Clippy concurrently.

    Defaults to HEAD versus local files. CI supplies --base and --head revisions.
    """
    sys.exit(
        commands.run_parallel(
            functools.partial(python.lint_python, base, head), rust.lint_rust
        )
    )
