"""Exclude example context captures from the docs-wide sparqld catalog."""

from __future__ import annotations

from mkdocs_macros_sparqld import server as sparqld_server

from docs_macros.discovery import EXAMPLE_CONTEXTS

_original_popen = []


def install():
    """Make the MkDocs sparqld process ignore example context captures."""
    if _original_popen:
        return
    _original_popen.append(sparqld_server.subprocess.Popen)
    sparqld_server.subprocess.Popen = _popen


def _popen(args, **kwargs):
    return _original_popen[0](_with_patterns(args), **kwargs)


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


def define_env(env):
    """MkDocs-macros pluglet entry: install exclusions before sparqld starts."""
    install()
