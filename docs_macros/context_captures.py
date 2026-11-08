"""Read a saved context document as one retrieval capture."""

import json
from datetime import datetime

from docs_macros.captures import UTC_OFFSET, UTC_SUFFIX, Capture, timestamp_id

DOCUMENT = "context.jsonld"
SCHEMA = "http://schema.org/"
CONTENT_SIZE = f"{SCHEMA}contentSize"
RETRIEVAL = f"{SCHEMA}result"
START = f"{SCHEMA}startTime"
END = f"{SCHEMA}endTime"
STATUS = f"{SCHEMA}actionStatus"
SUCCESS = "Success"


def read_context_capture(directory, identifier=None):
    document = json.loads((directory / DOCUMENT).read_text())
    action = _action(document)
    return _capture(directory, identifier, document, action)


def _capture(directory, identifier, document, action):
    started_text = _literal(action, START)
    started = _instant(started_text)
    ended = _instant(_literal(action, END))
    status = _status(action)
    address = document.get("@id")
    return Capture(
        directory=directory,
        identifier=identifier or timestamp_id(started_text),
        started=started,
        status=status,
        duration=max(0, (ended - started).total_seconds()),
        estimated_duration=True,
        error=None,
        byte_size=_size(document, status),
        endpoint=address if isinstance(address, str) else None,
    )


def _action(document):
    reverse = document.get("@reverse")
    action = reverse.get(RETRIEVAL) if isinstance(reverse, dict) else None
    if not isinstance(action, dict):
        raise ValueError(f"{document.get('@id', DOCUMENT)} has no retrieval action")
    return action


def _literal(node, key):
    recorded = node.get(key)
    if isinstance(recorded, dict):
        return recorded.get("@value")
    return recorded


def _instant(text):
    if not isinstance(text, str):
        raise ValueError("Context capture has no retrieval time")
    return datetime.fromisoformat(text.replace(UTC_SUFFIX, UTC_OFFSET))


def _status(action):
    node = action.get(STATUS) or {}
    identifier = str(node.get("@id", ""))
    name = identifier.rsplit("/", 1)[-1]
    return {
        "FailedActionStatus": "Failure",
        "ActiveActionStatus": "Incomplete",
        "CompletedActionStatus": SUCCESS,
    }.get(name, SUCCESS)


def _size(document, status):
    if status != SUCCESS:
        return None
    raw_size = _literal(document, CONTENT_SIZE)
    if isinstance(raw_size, bool) or not isinstance(raw_size, (str, int)):
        return None
    try:
        size = int(raw_size)
    except ValueError:
        return None
    return size if size >= 0 else None
