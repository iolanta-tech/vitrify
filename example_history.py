"""Discover saved retrievals and generate their documentation pages."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mkdocs.structure.files import File, InclusionLevel

ROOT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = ROOT_DIR / "docs" / "examples"
PAGE_EXAMPLES = {
    "eu-capitals": "basic-example",
    "query-from-file": "basic-example",
    "female-persons": "female-persons",
    "top-metaclasses": "top-metaclasses",
    "metaclasses-of-metaclasses": "metaclasses-of-metaclasses",
    "fourth-order-classes": "fourth-order-classes",
    "time-bounded-subclasses": "time-bounded-subclasses",
    "select-turtle": "select-turtle",
}
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{6}(?:\d{6})?Z\Z")


def timestamp_id(value):
    date = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return date.strftime("%Y-%m-%dT%H%M%S") + (date.strftime("%f") if date.microsecond else "") + "Z"


def property_value(entity, property_id, entities):
    properties = entity.get("additionalProperty", [])
    if isinstance(properties, dict):
        properties = [properties]
    resolved = [entities.get(item.get("@id"), item) for item in properties]
    return next((item.get("value") for item in resolved if item.get("propertyID") == property_id), None)


@dataclass(frozen=True)
class Capture:
    directory: Path
    identifier: str
    started: datetime
    status: str
    duration: float | None
    estimated_duration: bool
    row_count: int | None
    error: str | None
    byte_size: int | None = None


def legacy_row_count(directory, result):
    """Derive a display count from an existing capture without changing it."""
    count = 1
    with (directory / result["@id"]).open("rb") as response:
        while chunk := response.read(8192):
            count += chunk.count(b"\n")
    return count


def read_capture(directory, identifier=None):
    graph = json.loads((directory / "ro-crate-metadata.json").read_text())["@graph"]
    entities = {entity["@id"]: entity for entity in graph}
    action = entities["#retrieval"]
    started = datetime.fromisoformat(action["startTime"].replace("Z", "+00:00"))
    state = action.get("actionStatus", {}).get("@id", "")
    status = {"FailedActionStatus": "Failure", "ActiveActionStatus": "Incomplete", "CompletedActionStatus": "Success"}.get(state.rsplit("/", 1)[-1], "Success")
    duration = property_value(entities["./"], "retrieval-duration", entities)
    estimated = False
    if duration is None and action.get("endTime"):
        duration = max(0, (datetime.fromisoformat(action["endTime"].replace("Z", "+00:00")) - started).total_seconds())
        estimated = True
    result = entities.get(action.get("result", {}).get("@id"))
    count = property_value(result, "row-count", entities) if result else None
    software = entities.get(action.get("instrument", {}).get("@id"), {})
    # Version 0.1.0 recorded format-specific counts; derive text rows for those captures.
    if result and software.get("version") != "0.1.1":
        try:
            count = legacy_row_count(directory, result)
        except (ValueError, KeyError, OSError):
            count = None
    error = entities.get(action.get("error", {}).get("@id"), {}).get("description")
    raw_size = result.get("contentSize") if result and status == "Success" else None
    try:
        byte_size = int(raw_size) if isinstance(raw_size, (str, int)) and not isinstance(raw_size, bool) else None
    except ValueError:
        byte_size = None
    if byte_size is not None and byte_size < 0:
        byte_size = None
    return Capture(directory, identifier or timestamp_id(action["startTime"]), started, status, duration, estimated, count, error, byte_size)


def captures(example):
    directory = (EXAMPLES_DIR / example).resolve()
    if not directory.is_relative_to(EXAMPLES_DIR) or not directory.is_dir():
        raise ValueError(f"Invalid example directory: {example}")
    baseline = directory / "eu-capitals" if example == "basic-example" else directory
    result = []
    if (baseline / "ro-crate-metadata.json").is_file():
        result.append(read_capture(baseline))
    for child in sorted(directory.iterdir()):
        if child.is_dir() and TIMESTAMP.fullmatch(child.name) and (child / "ro-crate-metadata.json").is_file():
            result.append(read_capture(child, child.name))
    identifiers = [capture.identifier for capture in result]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"Duplicate attempt timestamp in {directory}")
    return sorted(result, key=lambda capture: (capture.started, capture.identifier))


def selected_capture(example, identifier=None):
    saved = captures(example)
    if not saved:
        raise ValueError(f"No saved retrievals for {example}")
    if identifier is None:
        return saved[-1]
    return next(capture for capture in saved if capture.identifier == identifier)


def on_files(files, config):
    """Generate permanent attempt pages from the existing example templates."""
    for page, example in PAGE_EXAMPLES.items():
        template = (EXAMPLES_DIR / f"{page}.md").read_text()
        for capture in captures(example):
            adjusted = re.sub(r"(\]\()(?!(?:[a-z]+:|/|#))([^\s)]+)", r"\1../\2", template)
            content = adjusted.replace("---\n", f"---\nhistory_attempt: {capture.identifier}\n", 1)
            files.append(File.generated(
                config, f"examples/{page}/{capture.identifier}.md",
                content=content, inclusion=InclusionLevel.NOT_IN_NAV,
            ))
    return files


def on_nav(nav, config, files):
    """Keep dated retrievals within their example's navigation section."""
    for file in files:
        if file.page is None or not file.src_uri.startswith("examples/"):
            continue
        parts = file.src_uri.split("/")
        if len(parts) != 3 or parts[1] not in PAGE_EXAMPLES:
            continue
        if not TIMESTAMP.fullmatch(Path(parts[2]).stem):
            continue
        canonical = files.get_file_from_path(f"examples/{parts[1]}.md")
        file.page.parent = canonical.page.parent
    return nav
