"""Build the sparqld query for one crate file's media type."""

from pathlib import Path
from urllib.parse import quote

DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"
METADATA = "ro-crate-metadata.json"


def encoding_format_query(crate_dir, file_name):
    graph = sparqld_iri(crate_dir / METADATA)
    file_iri = sparqld_iri(crate_dir / file_name)
    lines = (
        "PREFIX schema: <http://schema.org/>",
        "SELECT ?format WHERE {",
        "GRAPH <{graph}> {{".format(graph=graph),
        "<{file_iri}> a schema:MediaObject .".format(file_iri=file_iri),
        "OPTIONAL {",
        "<{file_iri}> schema:encodingFormat ?format".format(file_iri=file_iri),
        "}",
        "}",
        "}",
    )
    return "\n".join(lines)


def sparqld_iri(path):
    relative = path.resolve().relative_to(DOCS_DIR.resolve())
    encoded = quote(relative.as_posix(), safe="/")
    return "sparqld:{encoded}".format(encoded=encoded)
