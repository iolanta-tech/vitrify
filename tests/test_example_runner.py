"""Run page-defined requests against local HTTP success and failure fixtures."""

import contextlib
import io
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sh

from jeeves import runner as example_runner
from docs_macros.definitions import ContextExample, Example
from history_fixtures import HistoryFixture, PRIMARY, SECONDARY
from fixture import RecordedCall

from catalog_fixtures import QUERY

CSV_MEDIA_TYPE = "text/csv"
EXIT_STATUS_LIMIT = 256
ANY_EXIT = range(EXIT_STATUS_LIMIT)


class EndpointHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"@context":{"name":"http://example.org/name"}}\n'
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/ld+json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        query = self.rfile.read(int(self.headers["Content-Length"]))
        request = (self.path, query, self.headers.get("Accept"))
        self.server.received.append(request)
        self.send_response(
            {
                "/failure": HTTPStatus.SERVICE_UNAVAILABLE,
                "/gateway-timeout": HTTPStatus.GATEWAY_TIMEOUT,
                "/rate-limit": HTTPStatus.TOO_MANY_REQUESTS,
            }.get(self.path, HTTPStatus.OK)
        )
        self.send_header("Content-Type", CSV_MEDIA_TYPE)
        self.end_headers()
        self.wfile.write(b"s\nhttps://example.org/item\n")

    def log_message(self, *arguments):
        """Keep fixture request logging in the captured request list."""


def _assert_recorded_requests(test, before):
    assert before == test.baseline_bytes()
    assert len(test.server.received) == 8
    queries = [request[1] for request in test.server.received]
    assert set(queries) == {QUERY.encode("utf-8")}
    accepted = [request[2] for request in test.server.received]
    assert accepted == [
        CSV_MEDIA_TYPE,
        CSV_MEDIA_TYPE,
        None,
        None,
        CSV_MEDIA_TYPE,
        CSV_MEDIA_TYPE,
        None,
        None,
    ]


class RunnerTests(HistoryFixture):
    def setup_method(self):
        super().setup_method()
        sh.cargo("build", "--quiet")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), EndpointHandler)
        self.server.received = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.add_cleanup(self.server.server_close)
        self.add_cleanup(self.server.shutdown)
        port = self.server.server_port
        self.base = f"http://127.0.0.1:{port}"
        self.endpoints = (f"{self.base}/failure", f"{self.base}/success")

    def test_runner_continues_and_preserves_history(self, monkeypatch):
        definitions = {
            name: Example(
                name, name, QUERY, self.endpoints, "csv" if name == PRIMARY else None
            )
            for name in (PRIMARY, SECONDARY)
        }
        before = self.baseline_bytes()
        validate = RecordedCall(False)
        with monkeypatch.context() as context:
            context.setattr(example_runner, "_validate", validate)
            with contextlib.redirect_stdout(io.StringIO()):
                for _ in range(2):
                    assert example_runner.run_examples(definitions, self.root)
                assert validate.call_count == 8
        self._assert_captures()
        _assert_recorded_requests(self, before)

    def test_timeout_and_rate_limit_succeed(self, monkeypatch):
        endpoints = (
            f"{self.base}/gateway-timeout",
            f"{self.base}/rate-limit",
        )
        settings = Example("limits", "Limits", QUERY, endpoints)
        with monkeypatch.context() as context:
            context.setattr(example_runner, "_validate", RecordedCall(False))
            with contextlib.redirect_stdout(io.StringIO()):
                failed = example_runner.run_examples(
                    {settings.name: settings}, self.root
                )
        assert not failed
        captures = list((self.root / settings.name).iterdir())
        assert len(captures) == 2

    def test_context_example_saves_both(self):
        settings = ContextExample("annotation", "Annotation", f"{self.base}/success")
        with contextlib.redirect_stdout(io.StringIO()):
            assert not example_runner.run_examples({settings.name: settings}, self.root)
        attempts = list((self.root / settings.name).iterdir())
        assert len(attempts) == 1
        saved = attempts[0]
        document = json.loads((saved / "context.jsonld").read_text())
        assert document["@context"]["name"] == "http://example.org/name"
        assert "http://example.org/name" in (saved / "context.yamlld").read_text()

    def test_new_capture_directory(self, monkeypatch):
        settings = Example("new-example", "New example", QUERY, (self.endpoints[1],))
        with monkeypatch.context() as context:
            context.setattr(example_runner, "_validate", RecordedCall(False))
            with contextlib.redirect_stdout(io.StringIO()):
                assert not example_runner.run_examples(
                    {settings.name: settings}, self.root
                )
        attempts = list((self.root / settings.name).iterdir())
        assert len(attempts) == 1

    def test_generated_crates_validate(self):
        settings = Example("migration", "Migration", QUERY, self.endpoints, "csv")
        with contextlib.redirect_stdout(io.StringIO()):
            assert example_runner.run_examples({settings.name: settings}, self.root)
        attempts = list((self.root / settings.name).iterdir())
        assert len(attempts) == 2
        for attempt in attempts:
            document = json.loads((attempt / "ro-crate-metadata.json").read_text())
            assert document["@context"] == "https://w3id.org/ro/crate/1.3/context"
            validation = sh.Command("rocrate-validator")(
                "--no-interactive",
                "validate",
                "-p",
                "ro-crate-1.3",
                str(attempt),
                _ok_code=ANY_EXIT,
                _return_cmd=True,
            )
            assert validation.exit_code == 0, validation.stdout + validation.stderr

    def _assert_captures(self):
        for name in (PRIMARY, SECONDARY):
            attempts = [
                child for child in self.directory(name).iterdir() if child.is_dir()
            ]
            assert len(attempts) == 4
            for attempt in attempts:
                assert (attempt / "query.rq").read_bytes() == QUERY.encode("utf-8")
                assert _retrieval_status(attempt) in {
                    "FailedActionStatus",
                    "CompletedActionStatus",
                }


def _retrieval_status(attempt):
    graph = json.loads((attempt / "ro-crate-metadata.json").read_text())["@graph"]
    action = next(entity for entity in graph if entity["@id"] == "#retrieval")
    identifier = action["actionStatus"]["@id"]
    return identifier.rsplit("/", 1)[-1]
