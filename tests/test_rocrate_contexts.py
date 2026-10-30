"""Load current and historical RO-Crate contexts through sparqld."""

import json

from docs_macros.service import CatalogService
from catalog_fixtures import CatalogFixture


class CrateContextTests(CatalogFixture):
    def test_both_crate_contexts_load(self):
        for version in ("1.2", "1.3"):
            (self.root / f"crate-{version}.jsonld").write_text(
                json.dumps(
                    {
                        "@context": f"https://w3id.org/ro/crate/{version}/context",
                        "@graph": [
                            {
                                "@id": f"#metadata-{version}",
                                "@type": "CreativeWork",
                                "conformsTo": {
                                    "@id": f"https://w3id.org/ro/crate/{version}"
                                },
                            }
                        ],
                    }
                )
            )
        with CatalogService(self.root) as service:
            rows = service.query(
                "SELECT DISTINCT ?profile WHERE { "
                "?metadata <http://purl.org/dc/terms/conformsTo> ?profile }"
            )
        self.assertEqual(
            {row["profile"]["value"] for row in rows},
            {"https://w3id.org/ro/crate/1.2", "https://w3id.org/ro/crate/1.3"},
        )
