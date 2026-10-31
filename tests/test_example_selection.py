"""Select example pages for a partial retrieval."""

import unittest

from jeeves.examples import example_names_from_paths, select_examples

PAGE = "eu-capitals"
STORED = "capitals"


class SelectionTests(unittest.TestCase):
    def test_paths_keep_changed_example_pages(self):
        paths = [
            f"docs/examples/{PAGE}.md",
            "docs/examples/authoring.md",
            "docs/examples/index.md",
            "docs/examples/query-from-file.md",
            f"docs/examples/{PAGE}/2026-10-31T000000Z/query.rq",
            "docs/index.md",
        ]
        self.assertEqual(example_names_from_paths(paths), [PAGE])

    def test_select_examples_filters_named_pages(self):
        catalog = {PAGE: STORED, "other": "other"}
        self.assertEqual(select_examples(catalog, [PAGE]), {PAGE: STORED})

    def test_empty_names_keep_the_catalog(self):
        catalog = {PAGE: STORED}
        self.assertEqual(select_examples(catalog, []), catalog)

    def test_select_examples_rejects_an_unknown_name(self):
        with self.assertRaises(KeyError):
            select_examples({PAGE: STORED}, ["missing"])
