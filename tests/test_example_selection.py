"""Select example pages for a partial retrieval."""

import pytest

from jeeves.examples import example_names_from_paths, select_examples

PAGE = "eu-capitals"
STORED = "capitals"


class SelectionTests:
    def test_paths_keep_changed_example_pages(self):
        paths = [
            f"docs/examples/{PAGE}.md",
            "docs/examples/authoring.md",
            "docs/authoring.md",
            "docs/examples/index.md",
            "docs/examples/query-from-file.md",
            f"docs/examples/{PAGE}/2026-10-31T000000Z/query.rq",
            "docs/index.md",
        ]
        assert example_names_from_paths(paths) == [PAGE]

    def test_select_examples_filters_named_pages(self):
        catalog = {PAGE: STORED, "other": "other"}
        assert select_examples(catalog, [PAGE]) == {PAGE: STORED}

    def test_empty_names_keep_the_catalog(self):
        catalog = {PAGE: STORED}
        assert select_examples(catalog, []) == catalog

    def test_select_examples_rejects_an_unknown_name(self):
        with pytest.raises(KeyError):
            select_examples({PAGE: STORED}, ["missing"])
