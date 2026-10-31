"""Python formatting, style, tests, and repository checks."""

import sys

import rich

from docs_macros.catalog import load_catalog
from project_checks.commands import run_command
from project_checks.entrypoints import standalone_python_scripts
from project_checks.snapshots import changed_snapshots

MODULE_ARGUMENT = "-m"


def format_python():
    return run_command(
        sys.executable,
        MODULE_ARGUMENT,
        "ruff",
        "format",
        "--exit-non-zero-on-format",
        ".",
    )


def lint_python(base="HEAD", head=""):
    load_catalog()
    style_status = max(
        run_command(sys.executable, MODULE_ARGUMENT, "flake8", "."),
        run_command(sys.executable, MODULE_ARGUMENT, "ruff", "check", "."),
    )
    context_status = run_command(
        sys.executable, MODULE_ARGUMENT, "yamllint", "--strict", "docs/contexts"
    )
    violations = standalone_python_scripts()
    test_status = run_command(
        sys.executable,
        MODULE_ARGUMENT,
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
    )
    changed = changed_snapshots(base, head)
    _report(violations, changed)
    return max(
        style_status, context_status, test_status, int(bool(violations or changed))
    )


def _report(violations, changed):
    if violations:
        rich.print(
            "Expose project commands through Jeeves instead of standalone Python entry points:"
        )
        rich.print("\n".join(violations))
    if changed:
        rich.print("Existing example snapshots are immutable:")
        rich.print("\n".join(changed))
        rich.print("Save a new capture in a new timestamped directory instead.")
    else:
        rich.print("Existing example snapshots are unchanged.")
