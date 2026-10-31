"""Run the documented examples and validate each saved crate."""

import sys
from pathlib import Path

from docs_macros.catalog import load_catalog
from jeeves.runner import run_examples

PROJECT_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_DIR / "docs" / "examples"


def examples() -> None:
    """Append one retrieval per endpoint for every example and validate each crate."""
    if run_examples(load_catalog(EXAMPLES_DIR.parent), EXAMPLES_DIR):
        sys.exit(1)
