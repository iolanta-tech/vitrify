"""Project tasks for Vitrify. Run with `j <task>` (see https://jeeves.sh)."""

import sys
from pathlib import Path

import rich
import sh

PROFILE = "ro-crate-1.2"
PROJECT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = PROJECT_DIR / "docs" / "examples"

EXAMPLES = (
    ("female-persons", "retrieve.sh", "."),
    ("top-metaclasses", "retrieve.sh", "."),
    ("metaclasses-of-metaclasses", "retrieve.sh", "."),
    ("fourth-order-classes", "retrieve.sh", "."),
    ("select-turtle", "retrieve.sh", "."),
    ("time-bounded-subclasses", "retrieve.sh", "."),
    ("basic-example", "input/retrieve.sh", "eu-capitals"),
)


def examples() -> None:
    """Run the displayed retrieval scripts and validate every example crate."""
    for name, script_path, crate_path in EXAMPLES:
        directory = EXAMPLES_DIR / name
        rich.print(f"[b]{name}[/b]: running retrieval script…")
        sh.Command("sh")(
            str(directory / script_path),
            _cwd=str(directory if script_path.startswith("input/") else EXAMPLES_DIR),
            _err=sys.stderr,
        )
        rich.print(f"[b]{name}[/b]: validating {PROFILE}…")
        sh.Command("rocrate-validator").validate(
            "-p", PROFILE,
            str(directory / crate_path),
            _out=sys.stdout,
            _err=sys.stderr,
        )
        rich.print(f"[green]✓[/green] {name}: regenerated")


def serve() -> None:
    """Serve the Vitrify docs at http://localhost:6453."""
    sh.mkdocs.serve(
        "-a",
        "localhost:6453",
        _fg=True,
    )
