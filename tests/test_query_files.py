"""Check that editing a stored SPARQL query refreshes its cached text."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from docs_macros import query_files

FIRST_REVISION = 1_000_000_000
SECOND_REVISION = 2_000_000_000


class QueryFileTests(unittest.TestCase):
    def test_changed_file_refreshes_cache(self):
        with tempfile.TemporaryDirectory(prefix="vitrify-query-test-") as temporary:
            source = Path(temporary) / "example.rq"
            source.write_text("ASK {}\n", encoding="utf-8")
            os.utime(source, ns=(FIRST_REVISION, FIRST_REVISION))
            with patch.object(query_files, "QUERIES_DIR", source.parent):
                self.assertEqual(query_files.load_query(source.name), "ASK {}\n")
                source.write_text("SELECT ?s WHERE { ?s ?p ?o }\n", encoding="utf-8")
                os.utime(source, ns=(SECOND_REVISION, SECOND_REVISION))
                self.assertEqual(
                    query_files.load_query(source.name),
                    source.read_text(encoding="utf-8"),
                )
