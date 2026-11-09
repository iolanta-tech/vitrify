"""Exclude example context captures from the docs-wide sparqld catalog."""

from __future__ import annotations

import mkdocs_macros_sparqld.server as sparqld_server

from docs_macros.discovery import EXAMPLE_CONTEXTS

_state = {"original_popen": None}


def install():
    """Make the MkDocs sparqld process ignore example context captures."""
    if _state["original_popen"] is not None:
        return
    _state["original_popen"] = sparqld_server.subprocess.Popen
    sparqld_server.subprocess.Popen = _popen


def _popen(args, **kwargs):
    return _state["original_popen"](_with_patterns(args), **kwargs)


def _with_patterns(args):
    command = [str(part) for part in args]
    if len(command) < 2 or command[-1] != "--no-watch":
        return args
    if "sparqld" not in command[0]:
        return args
    prefixed = command[:-1]
    for pattern in EXAMPLE_CONTEXTS:
        prefixed.extend(("--pattern", pattern))
    prefixed.append("--no-watch")
    return prefixed
