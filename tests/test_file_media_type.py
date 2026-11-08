"""Read a crate file media type from the sparqld dataset."""

import json

from docs_macros.rendering import artifacts
from docs_macros.rendering.directories import _tree_lines
from fixture import RecordedCall

CRATE = artifacts.ROOT_DIR / "docs/examples/basic-example/eu-capitals"
FILE_IRI = "sparqld:examples/basic-example/eu-capitals/results.csv"
EMPTY_RESULTS = '{"head": {"vars": ["format"]}, "results": {"bindings": []}}'


class FileMediaTypeTests:
    def test_unindexed_file_media_type_is_empty(self, monkeypatch):
        with monkeypatch.context() as context:
            context.setattr(
                artifacts,
                "run_query",
                RecordedCall(("application/sparql-results+json", EMPTY_RESULTS)),
            )
            assert artifacts.file_media_type(CRATE, "query.rq") == ""

    def test_directory_with_unindexed_files_renders(self, monkeypatch):
        with monkeypatch.context() as context:
            context.setattr(
                artifacts,
                "run_query",
                RecordedCall(("application/sparql-results+json", EMPTY_RESULTS)),
            )
            preview = "\n".join(_tree_lines(CRATE))
        assert "[`query.rq`](#file-queryrq)" in preview
        assert "[`results.csv`](#file-resultscsv)" in preview

    def test_metadata_file_is_json_ld(self):
        media_type = artifacts.file_media_type(CRATE, artifacts.METADATA)
        assert media_type == "application/ld+json"

    def test_result_media_type_comes_from_sparqld(self, monkeypatch):
        body = json.dumps(
            {
                "head": {"vars": ["format"]},
                "results": {
                    "bindings": [
                        {
                            "format": {
                                "type": "literal",
                                "value": "text/csv",
                            },
                        },
                    ],
                },
            },
        )
        query = RecordedCall(("application/sparql-results+json", body))
        with monkeypatch.context() as context:
            context.setattr(artifacts, "run_query", query)
            media_type = artifacts.file_media_type(CRATE, "results.csv")
            asked = query.arguments[0]
        assert media_type == "text/csv"
        assert FILE_IRI in asked
        assert "schema:MediaObject" in asked
        assert "schema:encodingFormat" in asked
