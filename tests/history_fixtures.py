"""Shared saved-capture fixtures for history and runner tests."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from docs_macros import history as example_history

METADATA = "ro-crate-metadata.json"
RESULT_FILE = "results.csv"
QUERY = "query.rq"
PRIMARY = "first"
SECONDARY = "second"
GRAPH = "@graph"
IDENTIFIER = "@id"
RETRIEVAL = "#retrieval"
WDQS = "wdqs"
QLEVER = "qlever"
EXECUTABLE_MODE = 0o755


class HistoryFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="vitrify-history-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = example_history.EXAMPLES_DIR / "female-persons"
        self.baseline_files = (QUERY, RESULT_FILE, METADATA)
        for name in (PRIMARY, SECONDARY):
            directory = self.root / name
            directory.mkdir()
            for filename in self.baseline_files:
                shutil.copyfile(self.fixture / filename, directory / filename)

    def directory(self, name=PRIMARY):
        return self.root / name

    def entities(self, directory=None):
        directory = directory or self.directory()
        graph = json.loads((directory / METADATA).read_text())[GRAPH]
        return {entity[IDENTIFIER]: entity for entity in graph}

    def save(self, entities, directory=None):
        directory = directory or self.directory()
        document = {GRAPH: list(entities.values())}
        (directory / METADATA).write_text(json.dumps(document))

    def baseline_bytes(self):
        return {
            name: (self.directory() / name).read_bytes() for name in self.baseline_files
        }

    def failed_capture(self):
        directory = self.directory() / "2026-10-15T120000Z"
        directory.mkdir()
        entities = self.entities()
        entities[RETRIEVAL].update(
            {
                "startTime": "2026-10-15T12:00:00Z",
                "endTime": "2026-10-15T12:00:05Z",
                "actionStatus": {IDENTIFIER: "http://schema.org/FailedActionStatus"},
                "error": {IDENTIFIER: "#error"},
            }
        )
        entities[RETRIEVAL].pop("result")
        entities["#error"] = {
            IDENTIFIER: "#error",
            "@type": "Thing",
            "description": "HTTP 503",
        }
        self.save(entities, directory)

    def newer_capture(self, publisher):
        directory = self.directory() / "2026-10-16T120000Z"
        shutil.copytree(
            self.directory(), directory, ignore=shutil.ignore_patterns("2026-*")
        )
        entities = self.entities(directory)
        entities["./"]["publisher"][IDENTIFIER] = publisher
        entities[RETRIEVAL]["startTime"] = "2026-10-16T12:00:00Z"
        self.save(entities, directory)
        return directory
