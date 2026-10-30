"""Exercise real Markdown-LD loading and automatic example registration."""

import subprocess
from dataclasses import replace
from unittest.mock import patch

from mkdocs.config import load_config
from mkdocs.structure.files import File, Files

from docs_macros import catalog as example_catalog
from docs_macros import history as example_history
from docs_macros import site as example_site
from docs_macros.definitions import Example
from docs_macros.request_macros import RequestMacros
from catalog_fixtures import (
    CatalogFixture,
    ROOT,
    ENDPOINT,
    QUERY,
    NEW_EXAMPLE,
    SOURCE,
    QUERY_PROPERTY,
    ENDPOINTS,
)


class CatalogTests(CatalogFixture):
    def test_registered_context_and_implicit_identity(self):
        self.page(endpoints=[ENDPOINT, "https://another.example/sparql", ENDPOINT])
        settings = example_catalog.load_catalog(self.root)[NEW_EXAMPLE]
        self.assertEqual(settings.query, QUERY)
        self.assertIsNone(settings.format)
        self.assertEqual(
            settings.endpoints,
            tuple(sorted({ENDPOINT, "https://another.example/sparql"})),
        )
        self.assertNotIn("--format", settings.arguments(ENDPOINT))

    def test_migrated_definitions(self):
        definitions = example_catalog.load_catalog()
        migrated = {
            "female-persons",
            "time-bounded-subclasses",
            "select-turtle",
            "eu-capitals",
            "fourth-order-classes",
            "metaclasses-of-metaclasses",
            "top-metaclasses",
        }
        self.assertTrue(migrated <= definitions.keys())
        self.assertNotIn("query-from-file", definitions)
        for name in migrated:
            settings = definitions[name]
            self.assertNotRegex(settings.query, r"(?i)\bLIMIT\s+\d+")
            self.assertEqual(len(settings.endpoints), 2)

    def test_incomplete_definitions_fail(self):
        for metadata in (
            {"query": ""},
            {"endpoints": []},
            {"format": "unknown"},
            {"query": 42},
            {"endpoints": [42]},
            {"@context": {}},
            {"format": ["csv", "json"]},
        ):
            with self.subTest(metadata=metadata):
                self.page(**metadata)
                with self.assertRaisesRegex(ValueError, SOURCE):
                    example_catalog.load_catalog(self.root)

    def test_missing_query_fails(self):
        path = self.page()
        path.write_text(
            '---\n"@context": urn:vitrify:examples\nendpoints: [https://example.org/sparql]\n---\n# Broken\n'
        )
        with self.assertRaisesRegex(ValueError, "query"):
            example_catalog.load_catalog(self.root)

    def test_multiple_definitions_fail(self):
        metadata = {"@graph": [{QUERY_PROPERTY: "ASK {}", ENDPOINTS: [ENDPOINT]}]}
        self.page(**metadata)
        with self.assertRaisesRegex(ValueError, "one executable definition"):
            example_catalog.load_catalog(self.root)

    def test_loader_errors_fail(self):
        metadata = {"@context": "urn:missing:context"}
        self.page(**metadata)
        with self.assertRaisesRegex(ValueError, "new-example.md"):
            example_catalog.load_catalog(self.root)


class DiscoveryTests(CatalogFixture):
    def test_command_query_bytes(self):
        settings = Example("example", "Example", QUERY, (ENDPOINT,))
        for query in (QUERY, QUERY.rstrip("\n")):
            command = replace(settings, query=query).command(ENDPOINT)
            command = command.split(" |\n", 1)[0]
            completed = subprocess.run(
                ["sh", "-c", command], check=True, capture_output=True
            )
            self.assertEqual(completed.stdout, query.encode("utf-8"))

    def test_new_page_registration(self):
        self.page()
        config = load_config(
            config_file=str(ROOT / "mkdocs.yml"), docs_dir=str(self.root)
        )
        config.plugins._current_plugin = "example_site"
        config.nav = [{"Examples": ["examples/index.md"]}]
        example_site.on_config(config)
        self.assertIn({"New example": SOURCE}, config.nav[0]["Examples"])
        files = Files(
            [
                File(
                    SOURCE,
                    str(self.root),
                    str(self.root / "site"),
                    True,
                )
            ]
        )
        with patch.object(example_history, "EXAMPLES_DIR", self.root / "examples"):
            example_site.on_files(files, config)
            self.assertIn(
                "retrieval_command('new-example')",
                files.get_file_from_path(SOURCE).content_string,
            )
            self.assertEqual(len(files), 2)
            self.assertEqual(example_history.captures(NEW_EXAMPLE), [])
        self.assertFalse((self.root / "examples" / NEW_EXAMPLE).exists())

    def test_new_page_index(self):
        self.page()
        example_catalog.configure_catalog(self.root)
        self.assertIn("[New example](new-example.md)", RequestMacros().examples_index())
