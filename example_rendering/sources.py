"""Render a repository source file as a linked code admonition."""

from textwrap import indent

from example_rendering.artifacts import ROOT_DIR

RO_CRATE_URL = "https://www.researchobject.org/ro-crate/"


def source(path, repo_url, title="Source", collapsed=False):
    source_path = (ROOT_DIR / path).resolve()
    if not source_path.is_relative_to(ROOT_DIR):
        raise ValueError(f"Invalid source path: {path}")
    if not source_path.is_file():
        raise ValueError(f"Documentation source does not exist: {path}")
    heading = _heading(source_path, repo_url, title)
    syntax = {".json": "json", ".rq": "sparql", ".sh": "bash"}.get(
        source_path.suffix.lower(), "text"
    )
    code = _code(source_path, syntax)
    marker = "???" if collapsed else "!!!"
    return f'{marker} example "{heading}"\n\n{code}\n'


def _heading(source_path, repo_url, title):
    if title.startswith("RO-Crate"):
        title = f"[RO-Crate]({RO_CRATE_URL}){title.removeprefix('RO-Crate')}"
    repository_path = source_path.relative_to(ROOT_DIR).as_posix()
    github_url = f"{repo_url.rstrip('/')}/blob/main/{repository_path}"
    return (
        f'{title}<span class="example-source-link" markdown>'
        f":fontawesome-brands-github: [`{source_path.name}`]({github_url})</span>"
    )


def _code(source_path, syntax):
    source_text = source_path.read_text().rstrip("\n")
    return indent(f"```{syntax}\n{source_text}\n```", "    ")
