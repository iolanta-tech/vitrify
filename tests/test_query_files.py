"""Check that editing a stored SPARQL query refreshes its cached text."""

import os
import tempfile
from pathlib import Path

from docs_macros import query_files

FIRST_REVISION = 1_000_000_000
SECOND_REVISION = 2_000_000_000


class QueryFileTests:
    def test_changed_file_refreshes_cache(self, monkeypatch):
        with tempfile.TemporaryDirectory(prefix="vitrify-query-test-") as temporary:
            source = Path(temporary) / "example.rq"
            source.write_text("ASK {}\n", encoding="utf-8")
            os.utime(source, ns=(FIRST_REVISION, FIRST_REVISION))
            with monkeypatch.context() as context:
                context.setattr(query_files, "QUERIES_DIR", source.parent)
                assert query_files.load_query(source.name) == "ASK {}\n"
                source.write_text("SELECT ?s WHERE { ?s ?p ?o }\n", encoding="utf-8")
                os.utime(source, ns=(SECOND_REVISION, SECOND_REVISION))
                assert query_files.load_query(source.name) == source.read_text(encoding="utf-8")
