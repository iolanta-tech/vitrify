"""Run the documented examples and validate each saved crate."""

import sys
from pathlib import Path

import rich

from docs_macros.catalog import load_catalog
from jeeves.runner import run_examples

PROJECT_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_DIR / "docs" / "examples"
EXAMPLES_PREFIX = "docs/examples/"
MARKDOWN = ".md"
SKIPPED_PAGES = ("authoring", "index", "query-from-file")


def examples(name: list[str] | None = None) -> None:
    """Append one retrieval per endpoint for selected examples and validate each crate."""
    catalog = load_catalog(EXAMPLES_DIR.parent)
    try:
        selected = select_examples(catalog, name or [])
    except KeyError as error:
        rich.print(f"[red]Unknown example: {error}[/red]")
        sys.exit(1)
    if run_examples(selected, EXAMPLES_DIR):
        sys.exit(1)


def select_examples(catalog, names):
    """Return the named examples, or the whole catalog when names is empty."""
    if not names:
        return catalog
    missing = [page for page in names if page not in catalog]
    if missing:
        raise KeyError(", ".join(missing))
    return {page: catalog[page] for page in names}


def example_names_from_paths(paths):
    """Return example page names for changed docs/examples/*.md files."""
    names = []
    for filepath in paths:
        page = _example_page(filepath)
        if page and page not in names:
            names.append(page)
    return names


def _example_page(filepath):
    prefix = EXAMPLES_PREFIX
    if not filepath.startswith(prefix) or filepath.count("/") != 2:
        return None
    filename = filepath.removeprefix(prefix)
    if not filename.endswith(MARKDOWN):
        return None
    page = filename.removesuffix(MARKDOWN)
    if page in SKIPPED_PAGES:
        return None
    return page
