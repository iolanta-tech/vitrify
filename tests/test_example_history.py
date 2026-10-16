"""Regression checks for immutable example capture and history discovery."""

import contextlib
import io
import json
import shutil
import os
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import example_history
import jeeves


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="vitrify-history-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = example_history.EXAMPLES_DIR / "female-persons"
        self.baseline_files = ("query.rq", "results.csv", "ro-crate-metadata.json")
        for name in ("first", "second"):
            directory = self.root / name
            directory.mkdir()
            for filename in self.baseline_files:
                shutil.copyfile(self.fixture / filename, directory / filename)

    def test_latest_failure_keeps_baseline_and_earlier_pages_available(self):
        baseline = self.root / "first"
        before = {name: (baseline / name).read_bytes() for name in self.baseline_files}
        directory = baseline / "2026-10-15T120000Z"
        directory.mkdir()
        graph = json.loads(before["ro-crate-metadata.json"])["@graph"]
        action = next(entity for entity in graph if entity["@id"] == "#retrieval")
        action.update({"startTime": "2026-10-15T12:00:00Z", "endTime": "2026-10-15T12:00:05Z", "actionStatus": {"@id": "http://schema.org/FailedActionStatus"}, "error": {"@id": "#error"}})
        action.pop("result")
        graph.append({"@id": "#error", "@type": "Thing", "description": "HTTP 503"})
        (directory / "ro-crate-metadata.json").write_text(json.dumps({"@graph": graph}))
        with patch.object(example_history, "EXAMPLES_DIR", self.root):
            captures = example_history.captures("first")
            latest = example_history.selected_capture("first")
            self.assertEqual(len(captures), 2)
            self.assertEqual(captures[0].row_count, before["results.csv"].count(b"\n") + 1)
            self.assertEqual(latest.status, "Failure")
            self.assertEqual(latest.error, "HTTP 503")
            self.assertIsNone(latest.row_count)
            self.assertEqual(example_history.selected_capture("first", captures[0].identifier), captures[0])
        self.assertEqual(before, {name: (baseline / name).read_bytes() for name in self.baseline_files})

    def test_flattened_metrics_and_new_unknown_counts(self):
        directory = self.root / "first"
        document = json.loads((directory / "ro-crate-metadata.json").read_text())
        entities = {entity["@id"]: entity for entity in document["@graph"]}
        entities["https://vitrify.iolanta.tech"]["version"] = "0.1.1"
        entities["#retrieval"]["actionStatus"] = {"@id": "http://schema.org/CompletedActionStatus"}
        entities["./"]["additionalProperty"] = [{"@id": "#retrieval-duration"}]
        entities["results.csv"]["additionalProperty"] = [{"@id": "#row-count"}]
        document["@graph"].extend([
            {"@id": "#retrieval-duration", "@type": "PropertyValue", "propertyID": "retrieval-duration", "value": 0.5},
            {"@id": "#row-count", "@type": "PropertyValue", "propertyID": "row-count", "value": 1},
        ])
        metadata = directory / "ro-crate-metadata.json"
        metadata.write_text(json.dumps(document))
        capture = example_history.read_capture(directory)
        self.assertEqual(capture.duration, 0.5)
        self.assertFalse(capture.estimated_duration)
        self.assertEqual(capture.row_count, 1)
        entities["results.csv"].pop("additionalProperty")
        metadata.write_text(json.dumps(document))
        self.assertIsNone(example_history.read_capture(directory).row_count)

    def test_runner_appends_and_continues_after_retrieval_failure(self):
        validator = self.root / "bin" / "rocrate-validator"
        validator.parent.mkdir()
        validator.write_text("#!/bin/sh\nexit 0\n")
        validator.chmod(0o755)
        for name in ("first", "second"):
            commands = [f"mkdir {name}"]
            commands.extend(f"cp {shlex.quote(str(self.fixture / filename))} {name}/" for filename in self.baseline_files)
            commands.append("exit 1" if name == "first" else "exit 0")
            (self.root / name / "retrieve.sh").write_text("\n".join(commands) + "\n")
        before = (self.root / "first" / "results.csv").read_bytes()
        environment = {"PATH": str(validator.parent) + os.pathsep + os.environ["PATH"]}
        with patch.object(jeeves, "EXAMPLES_DIR", self.root), patch.object(jeeves, "EXAMPLES", (("first", "retrieve.sh", "."), ("second", "retrieve.sh", "."))), patch.dict(os.environ, environment), contextlib.redirect_stdout(io.StringIO()):
            for _ in range(2):
                with self.assertRaises(SystemExit):
                    jeeves.examples()
        for name in ("first", "second"):
            attempts = [child for child in (self.root / name).iterdir() if child.is_dir()]
            self.assertEqual(len(attempts), 2)
            for attempt in attempts:
                self.assertEqual({file.name for file in attempt.iterdir()}, set(self.baseline_files))
        self.assertEqual((self.root / "first" / "results.csv").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
