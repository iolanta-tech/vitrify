"""Limit Python string expressions to three physical source lines."""

import ast

MAXIMUM_LINES = 3
DOCSTRING_SCOPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


class StringLinesChecker:
    """Expose the string-size convention through Flake8."""

    name = "vitrify-string-lines"
    version = "0.1.0"

    def __init__(self, tree):
        self.tree = tree

    def run(self):
        docstrings = set(_docstrings(self.tree))
        for node in _strings(self.tree):
            if id(node) in docstrings:
                continue
            count = node.end_lineno - node.lineno + 1
            if count > MAXIMUM_LINES:
                message = f"VIT001 String spans {count} source lines (maximum {MAXIMUM_LINES}); move text to a file"
                yield node.lineno, node.col_offset, message, type(self)


def _docstrings(tree):
    for scope in ast.walk(tree):
        docstring = _docstring(scope)
        if docstring is not None:
            yield id(docstring)


def _docstring(scope):
    if not isinstance(scope, DOCSTRING_SCOPES) or not scope.body:
        return None
    statement = scope.body[0]
    if not isinstance(statement, ast.Expr) or not isinstance(
        statement.value, ast.Constant
    ):
        return None
    return statement.value if isinstance(statement.value.value, str) else None


def _strings(node):
    if isinstance(node, ast.JoinedStr):
        yield node
        yield from _formatted_strings(node)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
        yield node
    else:
        for child in ast.iter_child_nodes(node):
            yield from _strings(child)


def _formatted_strings(node):
    for component in node.values:
        if isinstance(component, ast.FormattedValue):
            yield from _strings(component.value)
