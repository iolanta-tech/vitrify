"""Keep project command entry points in Jeeves."""

import ast
from pathlib import Path

import sh

PROJECT_DIR = Path(__file__).resolve().parents[1]


def standalone_python_scripts(repository=PROJECT_DIR):
    names = sh.git(
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        "*.py",
        _cwd=str(repository),
        _return_cmd=True,
    ).stdout
    violations = []
    for name in sorted(set(names.split(b"\0")) - {b""}):
        relative = Path(name.decode("utf-8", errors="surrogateescape"))
        source = repository / relative
        if relative.parts[0] != "tests" and source.is_file() and _entry_point(source):
            violations.append(str(relative))
    return violations


def _entry_point(source):
    source_text = source.read_text()
    first_line = source_text.splitlines()[0] if source_text else ""
    if first_line.startswith("#!") and "python" in first_line:
        return True
    return any(
        _main_guard(node)
        for node in ast.walk(ast.parse(source_text, filename=str(source)))
    )


def _main_guard(node):
    return isinstance(node, ast.If) and ast.unparse(node.test) in (
        "__name__ == '__main__'",
        "'__main__' == __name__",
    )
