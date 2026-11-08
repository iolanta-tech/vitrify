"""Exercise the CI guard against real Git trees in an isolated repository."""

import tempfile
from pathlib import Path

import pytest
import sh

from project_checks.snapshots import changed_snapshots
from project_checks.entrypoints import standalone_python_scripts
from fixture import Fixture


EXECUTABLE_MODE = 0o755
QUERY_FILE = "query.rq"
CURRENT_REVISION = "HEAD"
STAGE_COMMAND = "add"


class SnapshotRepository(Fixture):
    def setup_method(self):
        super().setup_method()
        temporary = tempfile.TemporaryDirectory(prefix="vitrify-snapshot-test-")
        self.add_cleanup(temporary.cleanup)
        self.repository = Path(temporary.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Snapshot test")
        self.git("config", "user.email", "snapshot-test@example.invalid")
        self.git("config", "core.filemode", "true")
        self.baseline = "docs/examples/example"
        self.capture = f"{self.baseline}/2026-10-16T120000123456Z"
        for directory in (self.baseline, self.capture):
            for name in ("ro-crate-metadata.json", QUERY_FILE, "results.csv"):
                self.write(f"{directory}/{name}", "original\n")
        self.write(f"{self.baseline}/retrieve.sh", "original\n")
        self.commit()
        self.base = self.git("rev-parse", CURRENT_REVISION)

    def git(self, *arguments):
        completed = sh.git(*arguments, _cwd=str(self.repository), _in="")
        return str(completed).strip()

    def write(self, name, source_text):
        destination = self.repository / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source_text)

    def commit(self):
        self.git(STAGE_COMMAND, "--all")
        self.git("commit", "--quiet", "-m", "Save test state")

    def changes(self):
        self.commit()
        return changed_snapshots(self.base, CURRENT_REVISION, self.repository)


class CommittedSnapshotTests(SnapshotRepository):
    def test_allows_new_captures_and_source_changes(self):
        self.write(
            f"{self.baseline}/2026-10-17T120000Z/ro-crate-metadata.json", "new capture"
        )
        self.write(f"{self.baseline}/2026-10-17T120000Z/results.csv", "new result")
        self.write(f"{self.baseline}/retrieve.sh", "updated script")
        self.write("docs/examples/example.md", "updated documentation")
        assert self.changes() == []

    def test_rejects_snapshot_edits(self):
        names = [
            f"{directory}/{name}"
            for directory in (self.baseline, self.capture)
            for name in (QUERY_FILE, "results.csv", "ro-crate-metadata.json")
        ]
        for name in names:
            self.write(name, "changed")
        assert self.changes() == sorted(names)

    def test_rejects_snapshot_deletions(self):
        names = [
            f"{self.capture}/{name}"
            for name in (QUERY_FILE, "results.csv", "ro-crate-metadata.json")
        ]
        for name in names:
            (self.repository / name).unlink()
        assert self.changes() == sorted(names)

    def test_rejects_renames_and_file_mode_changes(self):
        original = f"{self.capture}/results.csv"
        renamed = f"{self.capture}/results.tsv"
        (self.repository / original).rename(self.repository / renamed)
        query = f"{self.baseline}/query.rq"
        (self.repository / query).chmod(EXECUTABLE_MODE)
        assert self.changes() == sorted([original, renamed, query])

    def test_rejects_additions_to_existing_capture(self):
        names = [f"{self.capture}/extra/evidence.json", f"{self.baseline}/results.json"]
        for name in names:
            self.write(name, "added")
        assert self.changes() == sorted(names)

    def test_rejects_added_file_edits(self):
        name = f"{self.capture}/evidence.json"
        self.write(name, "original")
        self.commit()
        self.base = self.git("rev-parse", CURRENT_REVISION)
        self.write(name, "changed")
        assert self.changes() == [name]

    def test_missing_base_fails_instead_of_passing(self):
        with pytest.raises(sh.ErrorReturnCode):
            changed_snapshots("missing-ref", CURRENT_REVISION, self.repository)


class LocalSnapshotTests(SnapshotRepository):
    def test_empty_base_allows_initial_snapshots(self):
        empty = self.git("hash-object", "-t", "tree", "-w", "--stdin")
        assert changed_snapshots(empty, CURRENT_REVISION, self.repository) == []

    def test_local_snapshot_edits(self):
        edited = f"{self.capture}/query.rq"
        staged = f"{self.baseline}/results.csv"
        deleted = f"{self.capture}/ro-crate-metadata.json"
        added = f"{self.capture}/evidence.json"
        for name in (edited, staged, added):
            self.write(name, "changed")
        self.git(STAGE_COMMAND, staged)
        (self.repository / deleted).unlink()
        assert changed_snapshots(
            self.base,
            repository=self.repository,
        ) == sorted([edited, staged, deleted, added])

    def test_local_modes_and_symlinks(self):
        mode_changed = f"{self.baseline}/query.rq"
        linked = f"{self.capture}/results.csv"
        (self.repository / mode_changed).chmod(EXECUTABLE_MODE)
        (self.repository / linked).unlink()
        (self.repository / linked).symlink_to(QUERY_FILE)
        changed = changed_snapshots(self.base, repository=self.repository)
        assert changed == sorted([mode_changed, linked])

    def test_local_hidden_staged_edits(self):
        name = f"{self.capture}/query.rq"
        self.write(name, "staged change")
        self.git(STAGE_COMMAND, name)
        self.write(name, "original\n")
        assert changed_snapshots(self.base, repository=self.repository) == [name]

    def test_local_additions(self):
        self.write(
            f"{self.baseline}/2026-10-17T120000Z/ro-crate-metadata.json", "new capture"
        )
        self.write(f"{self.baseline}/retrieve.sh", "changed script")
        assert changed_snapshots(self.base, repository=self.repository) == []

    def test_standalone_entry_points_are_rejected(self):
        self.write("main_guard.py", 'if __name__ == "__main__":\n    pass\n')
        self.write("reverse_guard.py", 'if "__main__" == __name__:\n    pass\n')
        self.write("shebang.py", "#!/usr/bin/env python3\n")
        assert standalone_python_scripts(self.repository) == ["main_guard.py", "reverse_guard.py", "shebang.py"]

    def test_allows_tasks_modules_and_tests(self):
        self.write("jeeves.py", "def lint():\n    pass\n")
        self.write("library.py", "def transform(value):\n    return value\n")
        self.write("tests/test_example.py", 'if __name__ == "__main__":\n    pass\n')
        assert standalone_python_scripts(self.repository) == []


class GitPagerTests(SnapshotRepository):
    def test_pager_cannot_hide_snapshot_edits(self, monkeypatch):
        name = f"{self.capture}/{QUERY_FILE}"
        self.write(name, "changed snapshot")
        self.git(STAGE_COMMAND, name)
        monkeypatch.setenv("GIT_PAGER", "cat >/dev/null")
        monkeypatch.setenv("TERM", "xterm")
        changed = changed_snapshots(self.base, repository=self.repository)
        assert changed == [name]

