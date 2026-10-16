"""Python formatting, style, tests, and repository checks."""

import sys

import rich

from project_checks.commands import run_command
from project_checks.entrypoints import standalone_python_scripts
from project_checks.snapshots import changed_snapshots


def format_python():
    return run_command(
        sys.executable, "-m", "ruff", "format", "--exit-non-zero-on-format", "."
    )


def lint_python(base="HEAD", head=""):
    style_status = run_command(sys.executable, "-m", "flake8", ".")
    violations = standalone_python_scripts()
    test_status = run_command(
        sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"
    )
    changed = changed_snapshots(base, head)
    _report(violations, changed)
    return max(style_status, test_status, int(bool(violations or changed)))


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
