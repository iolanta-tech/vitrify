"""Keep dated views tied to recorded requests and endpoint URLs."""

from types import SimpleNamespace
from unittest.mock import patch

from docs_macros import catalog as example_catalog
from docs_macros import history as example_history
from docs_macros.definitions import Example
from docs_macros.endpoints import ENDPOINTS, endpoint_key
from docs_macros.request_macros import RequestMacros
from docs_macros.requests import request_notice, saved_request
from docs_macros.site import _variants
from history_fixtures import HistoryFixture, PRIMARY, IDENTIFIER, RETRIEVAL, QLEVER

OLD_ENDPOINT = "https://old.example/sparql"


class RequestTests(HistoryFixture):
    def setUp(self):
        super().setUp()
        self.settings = Example(PRIMARY, "Example", "ASK {}\n", (OLD_ENDPOINT,), "json")

    def test_saved_query_and_format(self):
        capture = example_history.read_capture(self.directory())
        saved = saved_request(capture, self.settings)
        self.assertEqual(
            saved.query.encode("utf-8"), (self.directory() / "query.rq").read_bytes()
        )
        self.assertEqual(saved.format, "csv")
        self.assertIn("earlier query", request_notice(capture, self.settings))
        self.assertEqual(request_notice(capture, saved), "")

    def test_unknown_and_omitted_accept(self):
        entities = self.entities()
        for description, expected in (
            ("Accept: application/custom", False),
            ("HTTP 200", False),
            ("Accept: omitted", True),
        ):
            entities[RETRIEVAL]["description"] = description
            self.save(entities)
            saved = saved_request(
                example_history.read_capture(self.directory()), self.settings
            )
            self.assertEqual(saved is not None, expected)
            if saved is not None:
                self.assertIsNone(saved.format)

    def test_removed_endpoint_keeps_routes(self):
        self.newer_capture(OLD_ENDPOINT)
        with (
            patch.object(example_history, "EXAMPLES_DIR", self.root),
            patch.object(
                example_catalog.state, "definitions", {PRIMARY: self.settings}
            ),
        ):
            self.assertEqual(
                example_history.endpoints(PRIMARY),
                sorted([OLD_ENDPOINT, ENDPOINTS[QLEVER][1]]),
            )
            routes = [path for path, _, _ in _variants(PRIMARY)]
            self.assertIn("qlever.md", routes)
            self.assertIn(f"{endpoint_key(OLD_ENDPOINT)}.md", routes)
            self.assertEqual(len(example_history.captures(PRIMARY, OLD_ENDPOINT)), 1)

    def test_dated_command_uses_saved_request(self):
        capture = example_history.read_capture(self.directory())
        macros = RequestMacros()
        macros.environment = SimpleNamespace(
            page=SimpleNamespace(meta={"history_attempt": capture.identifier})
        )
        with (
            patch.object(example_history, "EXAMPLES_DIR", self.root),
            patch.object(
                example_catalog.state, "definitions", {PRIMARY: self.settings}
            ),
        ):
            command = macros.retrieval_command(PRIMARY)
            self.assertIn(ENDPOINTS[QLEVER][1], command)
            self.assertIn("--format csv", command)
            self.assertNotIn("ASK {}", command)
            self.assertEqual(
                macros.query_text(PRIMARY).encode("utf-8"),
                (self.directory() / "query.rq").read_bytes(),
            )

    def test_unknown_endpoint_has_no_guessed_command(self):
        entities = self.entities()
        entities["./"].pop("publisher")
        self.save(entities)
        capture = example_history.read_capture(self.directory())
        self.assertIsNone(capture.endpoint)
        self.assertIsNone(saved_request(capture, self.settings))
