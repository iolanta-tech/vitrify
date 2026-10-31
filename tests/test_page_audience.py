"""Query the audience recorded on a documentation page."""

import unittest
from pathlib import Path

from docs_macros.query_files import load_query
from docs_macros.service import CatalogService

from catalog_fixtures import CatalogFixture

USER = "user"
DOCUMENT = "document"
AUDIENCE = "audience"


def _audience_by_document(rows):
    audiences = {}
    for row in rows:
        audiences[row[DOCUMENT]["value"]] = row[AUDIENCE]["value"]
    return audiences


class PageAudienceTests(CatalogFixture):
    def test_guide_page_is_for_the_user(self):
        project = Path(__file__).resolve().parents[1]
        (self.root / "examples" / "authoring.md").write_text(
            (project / "docs/examples/authoring.md").read_text(encoding="utf-8")
        )
        (self.root / "AGENTS.md").write_text(
            (project / "docs/AGENTS.md").read_text(encoding="utf-8")
        )
        with CatalogService(self.root) as service:
            audiences = _audience_by_document(
                service.query(load_query("audiences.rq")),
            )
        self.assertEqual(audiences["sparqld:examples/authoring.md"], USER)
        self.assertEqual(audiences["sparqld:AGENTS.md"], "maintainer")


if __name__ == "__main__":
    unittest.main()
