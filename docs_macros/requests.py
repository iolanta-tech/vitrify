"""Read the request represented by a saved capture."""

import json
from dataclasses import replace

from docs_macros.definitions import FORMATS


def saved_request(capture, definition):
    query = capture.directory / "query.rq"
    if (
        not capture.endpoint
        or not query.is_file()
        or "Accept: " not in _description(capture)
    ):
        return None
    accept = _description(capture).split("Accept: ", 1)[1]
    formats = {media_type: name for name, media_type in FORMATS.items()}
    if accept != "omitted" and accept not in formats:
        return None
    return replace(
        definition, query=query.read_bytes().decode("utf-8"), format=formats.get(accept)
    )


def request_notice(capture, definition):
    saved = saved_request(capture, definition)
    if saved is None:
        return "Saved request details are incomplete. Inspect the query and RO-Crate metadata below."
    if saved.query != definition.query or saved.format != definition.format:
        return "This saved capture uses an earlier query or requested format. The command above uses the current definition."
    return ""


def _description(capture):
    graph = json.loads((capture.directory / "ro-crate-metadata.json").read_text())[
        "@graph"
    ]
    action = next(entity for entity in graph if entity["@id"] == "#retrieval")
    return action.get("description", "")
