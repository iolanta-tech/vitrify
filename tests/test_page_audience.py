"""Query the audience recorded on a documentation page."""

import unittest
from pathlib import Path

from docs_macros.query_files import load_query
from docs_macros.service import CatalogService

from catalog_fixtures import CatalogFixture

USER = "user"


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
            rows = service.query(load_query("audiences.rq"))
        audiences = {row["document"]["value"]: row["audience"]["value"] for row in rows}
        self.assertEqual(audiences["sparqld:examples/authoring.md"], USER)
        self.assertEqual(audiences["sparqld:AGENTS.md"], "maintainer")


if __name__ == "__main__":
    unittest.main()
