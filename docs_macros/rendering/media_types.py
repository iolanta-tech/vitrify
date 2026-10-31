"""Build the sparqld query for one crate file's media type."""

from pathlib import Path
from string import Template
from urllib.parse import quote

from docs_macros.query_files import load_query

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
METADATA = "ro-crate-metadata.json"


def encoding_format_query(crate_dir, file_name):
    graph = sparqld_iri(crate_dir / METADATA)
    file_iri = sparqld_iri(crate_dir / file_name)
    return Template(load_query("file-media-type.rq")).substitute(
        graph=graph, file_iri=file_iri
    )


def sparqld_iri(path):
    relative = path.resolve().relative_to(DOCS_DIR.resolve())
    encoded = quote(relative.as_posix(), safe="/")
    return "sparqld:{encoded}".format(encoded=encoded)
