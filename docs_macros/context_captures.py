"""Read a saved context document as one retrieval capture."""

from datetime import datetime
from string import Template

from docs_macros.captures import UTC_OFFSET, UTC_SUFFIX, Capture, timestamp_id
from docs_macros.query_files import load_query
from docs_macros.service import CatalogService

DOCUMENT = "context.jsonld"
GRAPH = "sparqld:context.jsonld"
SUCCESS = "Success"


def read_context_capture(directory, identifier=None):
    row = _row(directory)
    started_text = _field(row, "start")
    started = _instant(started_text)
    ended = _instant(_field(row, "end"))
    status = _status(_field(row, "status"))
    return Capture(
        directory=directory,
        identifier=identifier or timestamp_id(started_text),
        started=started,
        status=status,
        duration=max(0, (ended - started).total_seconds()),
        estimated_duration=True,
        error=None,
        byte_size=_size(row.get("size"), status),
        endpoint=_field(row, "url"),
    )


def _row(directory):
    query = Template(load_query("context-capture.rq")).substitute(graph=GRAPH)
    with CatalogService(directory) as service:
        rows = service.query(query)
    if not rows:
        location = (directory / DOCUMENT).as_posix()
        raise ValueError("No retrieval action in {0}".format(location))
    return rows[0]


def _field(row, name):
    return row[name]["value"]


def _instant(text):
    return datetime.fromisoformat(text.replace(UTC_SUFFIX, UTC_OFFSET))


def _status(identifier):
    name = identifier.rsplit("/", 1)[-1]
    return {
        "FailedActionStatus": "Failure",
        "ActiveActionStatus": "Incomplete",
        "CompletedActionStatus": SUCCESS,
    }.get(name, SUCCESS)


def _size(binding, status):
    if status != SUCCESS or binding is None:
        return None
    raw_size = binding["value"]
    if isinstance(raw_size, bool) or not isinstance(raw_size, (str, int)):
        return None
    try:
        size = int(raw_size)
    except ValueError:
        return None
    return size if size >= 0 else None
