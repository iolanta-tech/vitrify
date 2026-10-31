"""Regression checks for immutable capture history and measurements."""

from dataclasses import replace
from unittest.mock import patch

from docs_macros import catalog as example_catalog
from docs_macros import endpoints as example_endpoints
from docs_macros import history as example_history
from docs_macros.rendering import details, history

from history_fixtures import (
    HistoryFixture,
    RESULT_FILE,
    PRIMARY,
    IDENTIFIER,
    RETRIEVAL,
    WDQS,
    QLEVER,
)


class HistoryTests(HistoryFixture):
    def test_failure_preserves_history(self):
        before = self.baseline_bytes()
        self.failed_capture()
        with patch.object(example_history, "EXAMPLES_DIR", self.root):
            captures = example_history.captures(PRIMARY)
            latest = example_history.selected_capture(PRIMARY)
            self.assertEqual(len(captures), 2)
            self.assertEqual(captures[0].byte_size, len(before[RESULT_FILE]))
            self._assert_failure(latest)
            self.assertEqual(
                example_history.selected_capture(PRIMARY, captures[0].identifier),
                captures[0],
            )
        self.assertEqual(before, self.baseline_bytes())

    def test_byte_sizes_and_flattened_duration(self):
        entities = self.entities()
        entities[RETRIEVAL]["actionStatus"] = {
            IDENTIFIER: "http://schema.org/CompletedActionStatus"
        }
        entities["./"]["additionalProperty"] = [{IDENTIFIER: "#retrieval-duration"}]
        entities["#retrieval-duration"] = {
            IDENTIFIER: "#retrieval-duration",
            "@type": "PropertyValue",
            "propertyID": "retrieval-duration",
            "value": 0.5,
        }
        sizes = (
            ("1234", 1234),
            (0, 0),
            ("1", 1),
            (None, None),
            ("invalid", None),
            (-1, None),
            (True, None),
        )
        for size, expected in sizes:
            with self.subTest(size=size):
                entities[RESULT_FILE]["contentSize"] = size
                self.save(entities)
                self._assert_measurements(
                    example_history.read_capture(self.directory()), expected
                )

    def test_history_bytes_and_unknown_sizes(self):
        capture = example_history.read_capture(self.directory())
        saved = [
            replace(capture, identifier=str(index), byte_size=size)
            for index, size in enumerate((100, 50, 0, None))
        ]
        with (
            patch.object(history, "captures", return_value=saved),
            patch.object(history, "selected_capture", return_value=saved[0]),
        ):
            chart = history.history_chart("female-persons")
        self.assertIn("Response bytes", chart)
        self.assertIn("height:80.00px", chart)
        self.assertIn("height:40.00px", chart)
        self.assertIn("0 bytes", chart)
        self.assertEqual(chart.count('class="history-question"'), 1)
        self.assertNotIn("lines", chart)

    def _assert_failure(self, capture):
        self.assertEqual(capture.status, "Failure")
        self.assertEqual(capture.error, "HTTP 503")
        self.assertIsNone(capture.byte_size)

    def _assert_measurements(self, capture, expected):
        self.assertEqual(capture.duration, 0.5)
        self.assertFalse(capture.estimated_duration)
        self.assertEqual(capture.byte_size, expected)
        if expected is None:
            self.assertIn("Byte count unavailable", details.capture_detail(capture))
        else:
            unit = "byte" if expected == 1 else "bytes"
            self.assertIn(f"{expected:,} {unit}", details.capture_detail(capture))


class EndpointHistoryTests(HistoryFixture):
    def test_disjoint_endpoint_histories(self):
        with patch.object(example_history, "EXAMPLES_DIR", self.root):
            self._assert_endpoint_counts(1, 0)
            with self.assertRaises(ValueError):
                example_history.selected_capture(PRIMARY, endpoint=WDQS)
            newer = self.newer_capture(example_endpoints.ENDPOINTS[WDQS][1])
            self._assert_endpoint_counts(1, 1)
            self.assertEqual(
                example_history.selected_capture(PRIMARY, endpoint=WDQS).directory,
                newer,
            )
            self._remove_publisher(newer)
            self.assertEqual(example_history.captures(PRIMARY, WDQS), [])

    def test_commands_only_change_the_endpoint(self):
        definitions = example_catalog.configure_catalog()
        self.addCleanup(setattr, example_catalog.state, "definitions", None)
        for example in definitions:
            commands = self._commands(example)
            self.assertEqual(commands[0], commands[1])
            if definitions[example].format is None:
                self.assertNotIn("--format ", commands[0])
            else:
                self.assertIn("--format ", commands[0])
        command = example_endpoints.retrieval_command("basic-example", QLEVER)
        for prefix in ("wd:", "wdt:", "rdfs:"):
            self.assertIn(f"PREFIX {prefix}", command)

    def _assert_endpoint_counts(self, qlever, wdqs):
        self.assertEqual(len(example_history.captures(PRIMARY, QLEVER)), qlever)
        self.assertEqual(len(example_history.captures(PRIMARY, WDQS)), wdqs)

    def _remove_publisher(self, directory):
        entities = self.entities(directory)
        entities["./"].pop("publisher")
        self.save(entities, directory)

    def _commands(self, example):
        return [
            example_endpoints.retrieval_command(example, endpoint).replace(
                url, "ENDPOINT"
            )
            for endpoint, (_, url) in example_endpoints.ENDPOINTS.items()
        ]
