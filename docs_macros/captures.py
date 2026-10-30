"""Read recorded capture measurements without changing saved evidence."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


IDENTIFIER = "@id"
UTC_SUFFIX = "Z"
UTC_OFFSET = "+00:00"
RETRIEVAL = "#retrieval"


@dataclass(frozen=True)
class Capture:
    directory: Path
    identifier: str
    started: datetime
    status: str
    duration: float | None
    estimated_duration: bool
    error: str | None
    byte_size: int | None = None
    endpoint: str | None = None


def timestamp_id(timestamp_text):
    date = datetime.fromisoformat(
        timestamp_text.replace(UTC_SUFFIX, UTC_OFFSET)
    ).astimezone(timezone.utc)
    microseconds = date.strftime("%f") if date.microsecond else ""
    return f"{date.strftime('%Y-%m-%dT%H%M%S')}{microseconds}Z"


def property_value(entity, property_id, entities):
    properties = entity.get("additionalProperty", [])
    if isinstance(properties, dict):
        properties = [properties]
    resolved = [entities.get(entry.get(IDENTIFIER), entry) for entry in properties]
    return next(
        (
            entry.get("value")
            for entry in resolved
            if entry.get("propertyID") == property_id
        ),
        None,
    )


def _duration(entities):
    action = entities[RETRIEVAL]
    recorded = property_value(entities["./"], "retrieval-duration", entities)
    if recorded is None and action.get("endTime"):
        started = datetime.fromisoformat(
            action["startTime"].replace(UTC_SUFFIX, UTC_OFFSET)
        )
        ended = datetime.fromisoformat(
            action["endTime"].replace(UTC_SUFFIX, UTC_OFFSET)
        )
        return max(0, (ended - started).total_seconds()), True
    return recorded, False


def _byte_size(result_entity, status):
    raw_size = (
        result_entity.get("contentSize")
        if result_entity and status == "Success"
        else None
    )
    if isinstance(raw_size, bool) or not isinstance(raw_size, (str, int)):
        return None
    try:
        size = int(raw_size)
    except ValueError:
        return None
    return size if size >= 0 else None


def _capture_fields(entities):
    action = entities[RETRIEVAL]
    state = action.get("actionStatus", {}).get(IDENTIFIER, "")
    state = state.rsplit("/", 1)[-1]
    status = {
        "FailedActionStatus": "Failure",
        "ActiveActionStatus": "Incomplete",
        "CompletedActionStatus": "Success",
    }.get(state, "Success")
    result_entity = entities.get(action.get("result", {}).get(IDENTIFIER))
    error = entities.get(action.get("error", {}).get(IDENTIFIER), {})
    return {
        "status": status,
        "byte_size": _byte_size(result_entity, status),
        "error": error.get("description"),
    }


def read_capture(directory, identifier=None):
    entities = {
        entity[IDENTIFIER]: entity
        for entity in json.loads((directory / "ro-crate-metadata.json").read_text())[
            "@graph"
        ]
    }
    duration, estimated = _duration(entities)
    measurements = _capture_fields(entities)
    requested_endpoint = entities["./"].get("publisher", {}).get(IDENTIFIER)
    return Capture(
        directory=directory,
        identifier=identifier or timestamp_id(entities[RETRIEVAL]["startTime"]),
        started=datetime.fromisoformat(
            entities[RETRIEVAL]["startTime"].replace(UTC_SUFFIX, UTC_OFFSET)
        ),
        duration=duration,
        estimated_duration=estimated,
        **measurements,
        endpoint=requested_endpoint,
    )
