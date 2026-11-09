"""Regression checks for immutable capture history and measurements."""

import json
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

from docs_macros import catalog as example_catalog
from docs_macros import endpoints as example_endpoints
from docs_macros import history as example_history
from docs_macros.definitions import Example
from docs_macros.rendering import details, history

from fixture import Fixture, RecordedCall
from history_fixtures import (
    HistoryFixture,
    RESULT_FILE,
    PRIMARY,
    IDENTIFIER,
    RETRIEVAL,
    WDQS,
    QLEVER,
)


def _resized(capture):
    return [
        replace(capture, identifier=str(index), byte_size=size)
        for index, size in enumerate((100, 50, 0, None))
    ]


def _assert_byte_scale(chart):
    assert "Response bytes" in chart
    assert "height:80.00px" in chart
    assert "height:40.00px" in chart


def _assert_byte_marks(chart):
    assert "0 bytes" in chart
    assert chart.count('class="history-question"') == 1
    assert "lines" not in chart


class HistoryTests(HistoryFixture):
    def test_failure_preserves_history(self, monkeypatch):
        before = self.baseline_bytes()
        self.failed_capture()
        with monkeypatch.context() as context:
            context.setattr(example_history, "EXAMPLES_DIR", self.root)
            captures = example_history.captures(PRIMARY)
            latest = example_history.selected_capture(PRIMARY)
            assert len(captures) == 2
            assert captures[0].byte_size == len(before[RESULT_FILE])
            self._assert_failure(latest)
            assert example_history.selected_capture(PRIMARY, captures[0].identifier) == captures[0]
        assert before == self.baseline_bytes()

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
            entities[RESULT_FILE]["contentSize"] = size
            self.save(entities)
            self._assert_measurements(
                example_history.read_capture(self.directory()), expected
            )

    def test_history_bytes_and_unknown_sizes(self, monkeypatch):
        capture = example_history.read_capture(self.directory())
        saved = _resized(capture)
        with monkeypatch.context() as context:
            context.setattr(history, "captures", RecordedCall(saved))
            context.setattr(history, "selected_capture", RecordedCall(saved[0]))
            chart = history.history_chart("female-persons")
        _assert_byte_scale(chart)
        _assert_byte_marks(chart)

    def _assert_failure(self, capture):
        assert capture.status == "Failure"
        assert capture.error == "HTTP 503"
        assert capture.byte_size is None

    def _assert_measurements(self, capture, expected):
        assert str(capture.duration) == "0.5"
        assert not capture.estimated_duration
        assert capture.byte_size == expected
        if expected is None:
            assert "Byte count unavailable" in details.capture_detail(capture)
        else:
            unit = "byte" if expected == 1 else "bytes"
            assert f"{expected:,} {unit}" in details.capture_detail(capture)


class EndpointHistoryTests(HistoryFixture):
    def test_disjoint_endpoint_histories(self, monkeypatch):
        with monkeypatch.context() as context:
            context.setattr(example_history, "EXAMPLES_DIR", self.root)
            self._assert_endpoint_counts(1, 0)
            with pytest.raises(ValueError):
                example_history.selected_capture(PRIMARY, endpoint=WDQS)
            newer = self.newer_capture(example_endpoints.ENDPOINTS[WDQS][1])
            self._assert_endpoint_counts(1, 1)
            assert example_history.selected_capture(PRIMARY, endpoint=WDQS).directory == newer
            self._remove_publisher(newer)
            assert not example_history.captures(PRIMARY, WDQS)

    def test_commands_only_change_the_endpoint(self):
        definitions = example_catalog.configure_catalog()
        self.add_cleanup(setattr, example_catalog.state, "definitions", None)
        for example in definitions:
            if not isinstance(definitions[example], Example):
                continue
            commands = self._commands(example)
            assert commands[0] == commands[1]
            if definitions[example].format is None:
                assert "--format " not in commands[0]
            else:
                assert "--format " in commands[0]
        command = example_endpoints.retrieval_command("basic-example", QLEVER)
        for prefix in ("wd:", "wdt:", "rdfs:"):
            assert f"PREFIX {prefix}" in command

    def _assert_endpoint_counts(self, qlever, wdqs):
        assert len(example_history.captures(PRIMARY, QLEVER)) == qlever
        assert len(example_history.captures(PRIMARY, WDQS)) == wdqs

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


EXAMPLE = "dollar-convenience"
CONTEXT_URL = "https://json-ld.org/contexts/{0}.jsonld".format(EXAMPLE)
SCHEMA = "http://schema.org/"
BODY_BYTES = 803
MEASURED_SECONDS = 0.094461
DURATION_TOLERANCE = 0.001
EARLIER = "2026-11-08T150000000000Z"
LATER = "2026-11-08T160000000000Z"
LARGER = 100
SMALLER = 50


class ContextHistoryTests(Fixture):
    def setup_method(self):
        super().setup_method()
        temporary = tempfile.TemporaryDirectory(prefix="vitrify-context-history-")
        self.add_cleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.add_cleanup(setattr, example_catalog.state, "definitions", None)
        example_catalog.state.definitions = None

    def test_recorded_context_capture(self):
        directory = (
            example_history.EXAMPLES_DIR
            / "dollar-convenience"
            / "2026-11-09T075231394815Z"
        )
        capture = example_history.read_capture(directory, directory.name)
        assert (
            capture.identifier,
            capture.status,
            capture.byte_size,
            capture.endpoint,
            capture.estimated_duration,
        ) == (directory.name, "Success", BODY_BYTES, CONTEXT_URL, True)
        assert capture.duration == pytest.approx(
            MEASURED_SECONDS, abs=DURATION_TOLERANCE
        )

    def test_context_history_chart(self, monkeypatch):
        self._save(EARLIER, LARGER, "2026-11-08T15:00:00+00:00")
        self._save(LATER, SMALLER, "2026-11-08T16:00:00+00:00")
        with monkeypatch.context() as context:
            context.setattr(example_history, "EXAMPLES_DIR", self.root)
            chart = history.history_chart(EXAMPLE)
        assert "example-endpoints" not in chart
        assert "Query endpoint" not in chart
        assert chart.count('class="history-bar"') == len((LARGER, SMALLER))
        for text in ("height:80.00px", "height:40.00px", "100 bytes", LATER):
            assert text in chart

    def _save(self, identifier, size, started, url=CONTEXT_URL):
        directory = self.root / EXAMPLE / identifier
        directory.mkdir(parents=True)
        ended = started.replace(":00:00+", ":00:01+")
        document = json.dumps(self._document(size, started, ended, url))
        (directory / "context.jsonld").write_text(document)
        (directory / "context.yamlld").write_text(document)

    def _document(self, size, started, ended, url):
        action = {
            self._term("actionStatus"): {"@id": self._term("CompletedActionStatus")},
            self._term("startTime"): {"@value": started},
            self._term("endTime"): {"@value": ended},
        }
        return {
            self._term("contentUrl"): {"@id": url},
            self._term("contentSize"): {"@value": str(size)},
            "@reverse": {self._term("result"): action},
        }

    def _term(self, name):
        return SCHEMA + name
