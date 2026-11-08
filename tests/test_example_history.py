"""Regression checks for immutable capture history and measurements."""

from dataclasses import replace

import pytest

from docs_macros import catalog as example_catalog
from docs_macros import endpoints as example_endpoints
from docs_macros import history as example_history
from docs_macros.definitions import Example
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
from fixture import RecordedCall


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
