"""Discover saved retrievals and generate their documentation pages."""

import re
from pathlib import Path
from types import MappingProxyType

from example_endpoints import ENDPOINTS
from example_captures import Capture as Capture
from example_captures import read_capture
from example_pages import generated_files

ROOT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = ROOT_DIR / "docs" / "examples"
PAGE_EXAMPLES = MappingProxyType(
    {
        "eu-capitals": "basic-example",
        "query-from-file": "basic-example",
        "female-persons": "female-persons",
        "top-metaclasses": "top-metaclasses",
        "metaclasses-of-metaclasses": "metaclasses-of-metaclasses",
        "fourth-order-classes": "fourth-order-classes",
        "time-bounded-subclasses": "time-bounded-subclasses",
        "select-turtle": "select-turtle",
    }
)
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{6}(?:\d{6})?Z\Z")


def captures(example, endpoint=None):
    directory = (EXAMPLES_DIR / example).resolve()
    if not (directory.is_relative_to(EXAMPLES_DIR) and directory.is_dir()):
        raise ValueError(f"Invalid example directory: {example}")
    baseline = directory / "eu-capitals" if example == "basic-example" else directory
    saved_captures = []
    if (baseline / "ro-crate-metadata.json").is_file():
        saved_captures.append(read_capture(baseline))
    for child in sorted(directory.iterdir()):
        if _is_capture(child):
            saved_captures.append(read_capture(child, child.name))
    identifiers = [capture.identifier for capture in saved_captures]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"Duplicate attempt timestamp in {directory}")
    if endpoint is not None:
        saved_captures = [
            capture for capture in saved_captures if capture.endpoint == endpoint
        ]
    return sorted(
        saved_captures, key=lambda capture: (capture.started, capture.identifier)
    )


def selected_capture(example, identifier=None, endpoint=None):
    saved = captures(example, endpoint)
    if not saved:
        raise ValueError(f"No saved retrievals for {example}")
    if identifier is None:
        return saved[-1]
    return next(capture for capture in saved if capture.identifier == identifier)


def _is_capture(directory):
    return (
        directory.is_dir()
        and TIMESTAMP.fullmatch(directory.name)
        and (directory / "ro-crate-metadata.json").is_file()
    )


def _capture_order(capture):
    return capture.started, capture.identifier


def on_files(files, config):
    """Generate endpoint views and permanent retrieval pages from example templates."""
    for page, example in PAGE_EXAMPLES.items():
        for generated in generated_files(
            page,
            example,
            (EXAMPLES_DIR / f"{page}.md").read_text(),
            _variants(example),
            config,
        ):
            files.append(generated)
    return files


def _variants(example):
    variants = [(f"{endpoint}.md", endpoint, None) for endpoint in ENDPOINTS]
    for capture in captures(example):
        variants.append(
            (f"{capture.identifier}.md", capture.endpoint, capture.identifier)
        )
        if capture.endpoint:
            variants.append(
                (
                    f"{capture.endpoint}/{capture.identifier}.md",
                    capture.endpoint,
                    capture.identifier,
                )
            )
    return variants


def on_nav(nav, config, files):
    """Keep endpoint and dated views within their example's navigation section."""
    for page_file in files:
        if page_file.page and page_file.src_uri.startswith("examples/"):
            parts = page_file.src_uri.split("/")
            if len(parts) >= 3 and parts[1] in PAGE_EXAMPLES:
                canonical = files.get_file_from_path(f"examples/{parts[1]}.md")
                page_file.page.parent = canonical.page.parent
    return nav
