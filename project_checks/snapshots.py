"""Protect existing capture evidence in Git and in the working tree."""

import re
from pathlib import Path, PurePosixPath

import sh

PROJECT_DIR = Path(__file__).resolve().parents[1]
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{6}(?:\d{6})?Z\Z")
METADATA = "ro-crate-metadata.json"
EXAMPLE_FILES = "docs/examples/"
NULL_SEPARATOR = "-z"
OPTION_SEPARATOR = "--"


def _read_tree(revision, repository):
    tree = str(
        sh.git("rev-parse", "--verify", f"{revision}^{{tree}}", _cwd=str(repository))
    ).strip()
    entries = sh.git(
        "ls-tree",
        "-r",
        NULL_SEPARATOR,
        "--full-tree",
        tree,
        OPTION_SEPARATOR,
        EXAMPLE_FILES,
        _cwd=str(repository),
        _return_cmd=True,
    ).stdout
    return dict(_tree_entry(entry) for entry in entries.split(b"\0") if entry)


def _tree_entry(entry):
    attributes, name = entry.split(b"\t", 1)
    return PurePosixPath(name.decode("utf-8", errors="surrogateescape")), attributes


def _decode_paths(output):
    return {
        PurePosixPath(name.decode("utf-8", errors="surrogateescape"))
        for name in output.split(b"\0")
        if name
    }


def _local_changes(base, repository):
    changed = set()
    for command in (
        [
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
            NULL_SEPARATOR,
            base,
            OPTION_SEPARATOR,
            EXAMPLE_FILES,
        ],
        [
            "diff",
            "--name-only",
            "--no-renames",
            NULL_SEPARATOR,
            base,
            OPTION_SEPARATOR,
            EXAMPLE_FILES,
        ],
        [
            "ls-files",
            "--others",
            "--exclude-standard",
            NULL_SEPARATOR,
            OPTION_SEPARATOR,
            EXAMPLE_FILES,
        ],
    ):
        output = sh.git(*command, _cwd=str(repository), _return_cmd=True).stdout
        changed.update(_decode_paths(output))
    return changed


def _changed_paths(before, head, base, repository):
    if not head:
        return _local_changes(base, repository)
    after = _read_tree(head, repository)
    return {
        name
        for name in before.keys() | after.keys()
        if before.get(name) != after.get(name)
    }


def _protected(name, timestamped, baselines):
    if any(directory in name.parents for directory in timestamped):
        return True
    return name.parent in baselines and (
        name.name in (METADATA, "query.rq") or name.name.startswith("results.")
    )


def changed_snapshots(base, head="", repository=PROJECT_DIR):
    """Find changes to previously committed example snapshots.

    Snapshots preserve evidence of a retrieval, including the metadata produced by
    that version of Vitrify. Rewriting them to match a newer output schema changes
    the historical record. Update generators and documentation displays instead,
    and save new retrievals in new timestamped directories.

    The base revision defines existing snapshots. Freeze every file in an existing
    timestamped capture, including its file mode, and reject additions within it.
    For older baseline captures, protect metadata, query.rq, and results.* while
    allowing edits to adjacent retrieval scripts. New capture directories are allowed.

    With no head revision, compare the base to staged, unstaged, and untracked files.
    """
    before = _read_tree(base, repository)
    changed = _changed_paths(before, head, base, repository)
    directories = {name.parent for name in before if name.name == METADATA}
    timestamped = {
        directory for directory in directories if TIMESTAMP.fullmatch(directory.name)
    }
    baselines = directories - timestamped
    return sorted(
        str(name) for name in changed if _protected(name, timestamped, baselines)
    )
