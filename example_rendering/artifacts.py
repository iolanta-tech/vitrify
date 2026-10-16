"""Discover crate artifacts and their presentation metadata."""

import json
from pathlib import Path
from types import MappingProxyType
from textwrap import indent

from markdown.extensions.toc import slugify_unicode

ROOT_DIR = Path(__file__).resolve().parents[1]
METADATA = "ro-crate-metadata.json"
IDENTIFIER = "@id"
INDENTATION = "    "
PLAIN_TEXT = "text"
JSON_SYNTAX = "json"
SYNTAX = MappingProxyType(
    {".json": JSON_SYNTAX, ".rq": "sparql", ".ttl": "turtle", ".xml": "xml"}
)


def anchor_id(file_name):
    return slugify_unicode(f"file-{file_name}", "-")


def tab_input_id(file_name):
    return slugify_unicode(file_name, "-")


def crate_files(crate_dir):
    graph = json.loads((crate_dir / METADATA).read_text())["@graph"]
    action = next(entity for entity in graph if entity.get(IDENTIFIER) == "#retrieval")
    names = []
    if action.get("result"):
        names.append(action["result"][IDENTIFIER])
    names.extend((METADATA, "query.rq"))
    names.extend(
        entity[IDENTIFIER]
        for entity in graph
        if entity.get("@type") == "File"
        and entity.get(IDENTIFIER, "").startswith("results.")
        and entity[IDENTIFIER] not in names
    )
    return tuple(crate_dir / name for name in names if (crate_dir / name).is_file())


def file_media_type(crate_dir, file_name):
    if file_name == METADATA:
        return "application/ld+json"
    graph = json.loads((crate_dir / METADATA).read_text())["@graph"]
    entity = next(
        entity
        for entity in graph
        if entity.get("@type") == "File" and entity.get(IDENTIFIER) == file_name
    )
    return entity.get("encodingFormat", "")


def file_icon(file_name, media_type):
    if file_name == METADATA or "json" in media_type:
        return "material-code-json"
    return {"text/csv": "material-table", "text/turtle": "material-code-braces"}.get(
        media_type, "material-file-document-outline"
    )


def syntax_for(file_path):
    return SYNTAX.get(file_path.suffix.lower(), PLAIN_TEXT)


def code_block(source_text, syntax):
    code = indent(source_text.rstrip("\n"), INDENTATION)
    return f"    ```{syntax}\n{code}\n    ```\n"
