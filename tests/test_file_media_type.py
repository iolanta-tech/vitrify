"""Read a crate file media type from the sparqld dataset."""

import json
import unittest
from unittest.mock import patch

from docs_macros.rendering import artifacts

CRATE = artifacts.ROOT_DIR / "docs/examples/basic-example/eu-capitals"
FILE_IRI = "sparqld:examples/basic-example/eu-capitals/results.csv"


class FileMediaTypeTests(unittest.TestCase):
    def test_metadata_file_is_json_ld(self):
        media_type = artifacts.file_media_type(CRATE, artifacts.METADATA)
        self.assertEqual(media_type, "application/ld+json")

    def test_result_media_type_comes_from_sparqld(self):
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
        with patch.object(
            artifacts,
            "run_query",
            return_value=("application/sparql-results+json", body),
        ) as query:
            media_type = artifacts.file_media_type(CRATE, "results.csv")
            asked = query.call_args.args[0]
        self.assertEqual(media_type, "text/csv")
        self.assertIn(FILE_IRI, asked)
        self.assertIn("schema:MediaObject", asked)
        self.assertIn("schema:encodingFormat", asked)
