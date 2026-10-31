"""Discover saved retrievals and generate their documentation pages."""

import re
from pathlib import Path

from docs_macros.catalog import catalog
from docs_macros.captures import Capture as Capture
from docs_macros.captures import read_capture
from docs_macros.endpoints import endpoint_url
from docs_macros.storage import baseline_directory, storage_name

ROOT_DIR = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT_DIR / "docs" / "examples"
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{6}(?:\d{6})?Z\Z")


def captures(example, endpoint=None):
    directory = (EXAMPLES_DIR / storage_name(example)).resolve()
    if not directory.is_relative_to(EXAMPLES_DIR.resolve()):
        raise ValueError(f"Invalid example directory: {example}")
    if not directory.is_dir():
        return []
    baseline = baseline_directory(directory)
    saved = []
    if (baseline / "ro-crate-metadata.json").is_file():
        saved.append(read_capture(baseline))
    saved.extend(
        read_capture(child, child.name)
        for child in sorted(directory.iterdir())
        if _is_capture(child)
    )
    identifiers = [capture.identifier for capture in saved]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"Duplicate attempt timestamp in {directory}")
    if endpoint is not None:
        saved = [
            capture for capture in saved if capture.endpoint == endpoint_url(endpoint)
        ]
    return sorted(saved, key=lambda capture: (capture.started, capture.identifier))


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


def endpoints(example):
    current = catalog().get(example)
    configured = current.endpoints if current else ()
    recorded = (capture.endpoint for capture in captures(example) if capture.endpoint)
    return sorted(set(configured).union(recorded))
