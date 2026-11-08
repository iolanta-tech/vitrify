"""Keep dated views tied to recorded requests and endpoint URLs."""

from types import SimpleNamespace

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
    def setup_method(self):
        super().setup_method()
        self.settings = Example(PRIMARY, "Example", "ASK {}\n", (OLD_ENDPOINT,), "json")

    def test_saved_query_and_format(self):
        capture = example_history.read_capture(self.directory())
        saved = saved_request(capture, self.settings)
        assert saved.query.encode("utf-8") == (self.directory() / "query.rq").read_bytes()
        assert saved.format == "csv"
        assert "earlier query" in request_notice(capture, self.settings)
        assert request_notice(capture, saved) == ""

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
            assert (saved is not None) == expected
            if saved is not None:
                assert saved.format is None

    def test_removed_endpoint_keeps_routes(self, monkeypatch):
        self.newer_capture(OLD_ENDPOINT)
        with monkeypatch.context() as context:
            context.setattr(example_history, "EXAMPLES_DIR", self.root)
            context.setattr(
                example_catalog.state, "definitions", {PRIMARY: self.settings}
            )
            endpoints = example_history.endpoints(PRIMARY)
            assert endpoints == sorted([OLD_ENDPOINT, ENDPOINTS[QLEVER][1]])
            routes = [path for path, _, _ in _variants(PRIMARY)]
            assert "qlever.md" in routes
            assert f"{endpoint_key(OLD_ENDPOINT)}.md" in routes
            assert len(example_history.captures(PRIMARY, OLD_ENDPOINT)) == 1

    def test_dated_command_uses_saved_request(self, monkeypatch):
        capture = example_history.read_capture(self.directory())
        macros = RequestMacros()
        macros.environment = SimpleNamespace(
            page=SimpleNamespace(meta={"history_attempt": capture.identifier})
        )
        with monkeypatch.context() as context:
            context.setattr(example_history, "EXAMPLES_DIR", self.root)
            context.setattr(
                example_catalog.state, "definitions", {PRIMARY: self.settings}
            )
            command = macros.retrieval_command(PRIMARY)
            assert ENDPOINTS[QLEVER][1] in command
            assert "--format csv" in command
            assert "ASK {}" not in command
            saved_query = macros.query_text(PRIMARY).encode("utf-8")
            assert saved_query == (self.directory() / "query.rq").read_bytes()

    def test_unknown_endpoint_has_no_guessed_command(self):
        entities = self.entities()
        entities["./"].pop("publisher")
        self.save(entities)
        capture = example_history.read_capture(self.directory())
        assert capture.endpoint is None
        assert saved_request(capture, self.settings) is None
