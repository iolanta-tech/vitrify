"""Shared Markdown-LD catalog fixtures."""

import json
import shutil
import tempfile
from pathlib import Path

from docs_macros import catalog as example_catalog
from fixture import Fixture

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://example.org/sparql"
EXAMPLES = "examples"
NEW_EXAMPLE = "new-example"
QUERY_PROPERTY = "query"
ENDPOINTS = "endpoints"
SOURCE = "examples/new-example.md"
QUERY = "{query}\n".format(
    query=r'SELECT ?label WHERE { ?s ?p "Unicode: α; quote: \' ; slash: \\" }'
)


class CatalogFixture(Fixture):
    def setup_method(self):
        super().setup_method()
        self.temporary = tempfile.TemporaryDirectory(prefix="vitrify-catalog-test-")
        self.add_cleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / EXAMPLES).mkdir()
        shutil.copytree(ROOT / "docs" / "contexts", self.root / "contexts")
        self.add_cleanup(setattr, example_catalog.state, "definitions", None)

    def page(self, name=NEW_EXAMPLE, **metadata):
        document = {
            "@context": "urn:vitrify:examples",
            QUERY_PROPERTY: QUERY,
            ENDPOINTS: [ENDPOINT],
        }
        document.update(metadata)
        path = self.root / EXAMPLES / f"{name}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            + json.dumps(document, ensure_ascii=False, indent=2)
            + "\n---\n# New example\n\nExplanation.\n"
        )
        return path
