"""Rust formatting and warning-free Clippy checks."""

from project_checks.commands import PROJECT_DIR, run_command


def format_rust(repository=PROJECT_DIR):
    status = run_command(
        "cargo", "fmt", "--all", "--", "--check", repository=repository
    )
    if status == 1:
        applied = run_command("cargo", "fmt", "--all", repository=repository)
        return max(status, applied)
    return status


def lint_rust():
    return run_command(
        "cargo", "clippy", "--all-targets", "--all-features", "--", "-D", "warnings"
    )
