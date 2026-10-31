"""Read source metadata and SPARQL bindings for the example catalog."""

from urllib.parse import unquote

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from docs_macros.service import CatalogService
from docs_macros.query_files import load_query

VOCABULARY = "urn:vitrify:vocabulary:"
BINDING = "value"


def sources(directory):
    return {
        path.relative_to(directory).as_posix(): read_source(path)
        for path in sorted((directory / "examples").rglob("*.md"))
    }


def read_source(path):
    source = path.read_text(encoding="utf-8")
    if not source.startswith("---\n"):
        return source, {}
    parts = source.split("---\n", 2)
    if len(parts) != 3:
        raise ValueError(f"{path}: unclosed frontmatter")
    try:
        metadata = YAML(typ="safe", pure=True).load(parts[1])
    except YAMLError as error:
        raise ValueError(f"{path}: {error}") from error
    if not isinstance(metadata, dict):
        raise ValueError(f"{path}: frontmatter must be a mapping")
    return source, metadata


def discover(directory):
    with CatalogService(directory) as service:
        _check_errors(service.query(load_query("load-errors.rq")), directory)
        return _group(service.query(load_query("examples.rq")))


def _check_errors(errors, directory):
    failures = []
    for row in errors:
        source = row["source"][BINDING]
        path = directory / unquote(source.removeprefix("sparqld:"))
        if (
            path.name.startswith("results.")
            and (path.parent / "ro-crate-metadata.json").is_file()
        ):
            continue
        message = row["message"][BINDING]
        failures.append(f"{source}: {message}")
    if failures:
        raise ValueError("\n".join(failures))


def _group(rows):
    grouped = {}
    for row in rows:
        path = unquote(row["page"][BINDING].removeprefix("sparqld:"))
        properties = grouped.setdefault(path, {}).setdefault(
            row["definition"][BINDING], {}
        )
        bindings = properties.setdefault(
            row["property"][BINDING].removeprefix(VOCABULARY), []
        )
        if row[BINDING] not in bindings:
            bindings.append(row[BINDING])
    return grouped
