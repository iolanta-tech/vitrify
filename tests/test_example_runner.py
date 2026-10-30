"""Run page-defined requests against local HTTP success and failure fixtures."""

import contextlib
import io
import json
import subprocess
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from jeeves import runner as example_runner
from docs_macros.definitions import Example
from history_fixtures import HistoryFixture, PRIMARY, SECONDARY

from catalog_fixtures import QUERY

CSV_MEDIA_TYPE = "text/csv"


class EndpointHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        query = self.rfile.read(int(self.headers["Content-Length"]))
        request = (self.path, query, self.headers.get("Accept"))
        self.server.received.append(request)
        self.send_response(
            HTTPStatus.SERVICE_UNAVAILABLE if self.path == "/failure" else HTTPStatus.OK
        )
        self.send_header("Content-Type", CSV_MEDIA_TYPE)
        self.end_headers()
        self.wfile.write(b"s\nhttps://example.org/item\n")

    def log_message(self, *arguments):
        """Keep fixture request logging in the captured request list."""


class RunnerTests(HistoryFixture):
    def setUp(self):
        super().setUp()
        subprocess.run(["cargo", "build", "--quiet"], check=True)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), EndpointHandler)
        self.server.received = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        port = self.server.server_port
        self.base = f"http://127.0.0.1:{port}"
        self.endpoints = (f"{self.base}/failure", f"{self.base}/success")

    def test_runner_continues_and_preserves_history(self):
        definitions = {
            name: Example(
                name, name, QUERY, self.endpoints, "csv" if name == PRIMARY else None
            )
            for name in (PRIMARY, SECONDARY)
        }
        before = self.baseline_bytes()
        with (
            patch.object(example_runner, "_validate", return_value=False) as validate,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            for _ in range(2):
                self.assertTrue(example_runner.run_examples(definitions, self.root))
            self.assertEqual(validate.call_count, 8)
        self.assertEqual(before, self.baseline_bytes())
        self.assertEqual(len(self.server.received), 8)
        queries = [request[1] for request in self.server.received]
        self.assertEqual(set(queries), {QUERY.encode("utf-8")})
        self.assertEqual(
            [request[2] for request in self.server.received],
            [
                CSV_MEDIA_TYPE,
                CSV_MEDIA_TYPE,
                None,
                None,
                CSV_MEDIA_TYPE,
                CSV_MEDIA_TYPE,
                None,
                None,
            ],
        )
        self._assert_captures()

    def test_new_capture_directory(self):
        settings = Example("new-example", "New example", QUERY, (self.endpoints[1],))
        with (
            patch.object(example_runner, "_validate", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertFalse(
                example_runner.run_examples({settings.name: settings}, self.root)
            )
        attempts = list((self.root / settings.name).iterdir())
        self.assertEqual(len(attempts), 1)

    def _assert_captures(self):
        for name in (PRIMARY, SECONDARY):
            attempts = [
                child for child in self.directory(name).iterdir() if child.is_dir()
            ]
            self.assertEqual(len(attempts), 4)
            for attempt in attempts:
                self.assertEqual(
                    (attempt / "query.rq").read_bytes(), QUERY.encode("utf-8")
                )
                graph = json.loads((attempt / "ro-crate-metadata.json").read_text())[
                    "@graph"
                ]
                action = next(
                    entity for entity in graph if entity["@id"] == "#retrieval"
                )
                self.assertIn(
                    action["actionStatus"]["@id"].rsplit("/", 1)[-1],
                    {"FailedActionStatus", "CompletedActionStatus"},
                )
