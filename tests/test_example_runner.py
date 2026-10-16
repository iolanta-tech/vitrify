"""Check that refreshes append captures and continue after failures."""

import contextlib
import io
import os
import shlex
from unittest.mock import patch

import jeeves

from history_fixtures import (
    HistoryFixture,
    PRIMARY,
    SECONDARY,
    RESULT_FILE,
    EXECUTABLE_MODE,
)

RETRIEVAL_SCRIPT = "retrieve.sh"


class RunnerTests(HistoryFixture):
    def test_runner_continues_after_failure(self):
        validator = self._validator()
        for name in (PRIMARY, SECONDARY):
            self._script(name)
        before = (self.directory() / RESULT_FILE).read_bytes()
        environment = {
            "PATH": os.pathsep.join((str(validator.parent), os.environ["PATH"]))
        }
        with (
            patch.object(jeeves, "EXAMPLES_DIR", self.root),
            patch.object(
                jeeves,
                "EXAMPLES",
                ((PRIMARY, RETRIEVAL_SCRIPT, "."), (SECONDARY, RETRIEVAL_SCRIPT, ".")),
            ),
            patch.dict(os.environ, environment),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self._run_twice()
        self._assert_attempts()
        self.assertEqual((self.directory() / RESULT_FILE).read_bytes(), before)

    def _validator(self):
        validator = self.root / "bin" / "rocrate-validator"
        validator.parent.mkdir()
        validator.write_text("#!/bin/sh\nexit 0\n")
        validator.chmod(EXECUTABLE_MODE)
        return validator

    def _script(self, name):
        commands = ["# --endpoint https://query.wikidata.org/sparql", f"mkdir {name}"]
        commands.extend(
            f"cp {shlex.quote(str(self.fixture / filename))} {name}/"
            for filename in self.baseline_files
        )
        commands.append("exit 1" if name == PRIMARY else "exit 0")
        script = "\n".join(commands)
        (self.root / name / RETRIEVAL_SCRIPT).write_text(f"{script}\n")

    def _run_twice(self):
        for _ in range(2):
            with self.assertRaises(SystemExit):
                jeeves.examples()

    def _assert_attempts(self):
        for name in (PRIMARY, SECONDARY):
            attempts = [
                child for child in self.directory(name).iterdir() if child.is_dir()
            ]
            self.assertEqual(len(attempts), 4)
            for attempt in attempts:
                self.assertEqual(
                    {artifact.name for artifact in attempt.iterdir()},
                    set(self.baseline_files),
                )
