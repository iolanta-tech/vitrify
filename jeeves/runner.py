"""Append endpoint retrievals and validate their saved crates."""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import rich
import sh

from docs_macros.definitions import ContextExample
from docs_macros.endpoints import endpoint_label
from docs_macros.storage import storage_name

TRANSIENT_HTTP_STATUSES = frozenset((429, 504))
RETRIEVAL_ID = "#retrieval"
MINIMUM_EXIT_CODE = -128
MAXIMUM_EXIT_CODE = 256
PROCESS_EXIT_CODES = range(MINIMUM_EXIT_CODE, MAXIMUM_EXIT_CODE)
PROJECT_DIR = Path(__file__).resolve().parents[1]


def run_examples(examples, directory):
    failed = False
    for example in examples.values():
        saved = directory / storage_name(example.name)
        if isinstance(example, ContextExample):
            failed |= _retrieve_context(example, saved)
            continue
        for endpoint in example.endpoints:
            failed |= _retrieve(example, endpoint, saved)
    return failed


def _environment():
    path_key = "PATH"
    local_binary = PROJECT_DIR / "target" / "debug" / "vitrify"
    environment = os.environ.copy()
    if local_binary.is_file():
        current = environment[path_key] if path_key in environment else ""
        environment[path_key] = os.pathsep.join((str(local_binary.parent), current))
    return environment


def _retrieve(example, endpoint, directory):
    name = example.name
    rich.print(f"[b]{name}[/b]: running {endpoint_label(endpoint)} retrieval…")
    with tempfile.TemporaryDirectory(prefix="vitrify-example-") as temporary:
        output = Path(temporary) / name
        completed = sh.Command(
            "vitrify", search_paths=_environment()["PATH"].split(os.pathsep)
        )(
            *example.arguments(endpoint, output),
            _in=example.query,
            _cwd=temporary,
            _env=_environment(),
            _out=sys.stdout,
            _err=sys.stderr,
            _ok_code=PROCESS_EXIT_CODES,
            _return_cmd=True,
        )
        if not (output / "ro-crate-metadata.json").is_file():
            rich.print(f"[red]{name}: no retrieval metadata was saved[/red]")
            return True
        destination = _save_capture(output, directory)
    if _validate(name, destination):
        return True
    return (
        completed.exit_code != 0
        and _http_status(destination) not in TRANSIENT_HTTP_STATUSES
    )


def _retrieve_context(example, directory):
    rich.print(f"[b]{example.name}[/b]: fetching {example.url}…")
    with tempfile.TemporaryDirectory(prefix="vitrify-context-") as temporary:
        (Path(temporary) / example.name).mkdir()
        for filename, extra in (
            ("context.jsonld", []),
            ("context.yamlld", ["--as", "yamlld"]),
        ):
            with (Path(temporary) / example.name / filename).open("wb") as stdout:
                completed = sh.Command(
                    "vitrify", search_paths=_environment()["PATH"].split(os.pathsep)
                )(
                    "context",
                    example.url,
                    *extra,
                    _cwd=temporary,
                    _env=_environment(),
                    _out=stdout,
                    _err=sys.stderr,
                    _ok_code=PROCESS_EXIT_CODES,
                    _return_cmd=True,
                )
            if completed.exit_code != 0:
                rich.print(f"[red]{example.name}: context retrieval failed[/red]")
                return True
        _save_capture(Path(temporary) / example.name, directory)
    return False


def _save_capture(output, directory):
    directory.mkdir(parents=True, exist_ok=True)
    while True:
        destination = directory / datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H%M%S%fZ"
        )
        try:
            destination.mkdir()
        except FileExistsError:
            continue
        break
    with tempfile.TemporaryDirectory(prefix=".pending-", dir=directory) as staging:
        shutil.copytree(output, staging, dirs_exist_ok=True)
        os.replace(staging, destination)
    return destination


def _http_status(destination):
    document = json.loads((destination / "ro-crate-metadata.json").read_text())
    action = next(
        entity for entity in document["@graph"] if entity.get("@id") == RETRIEVAL_ID
    )
    description = action["description"] if "description" in action else ""
    prefix = "HTTP "
    if not description.startswith(prefix):
        return None
    number = description.removeprefix(prefix).split(";", 1)[0]
    if not number.isdecimal():
        return None
    return int(number)


def _validate(name, destination):
    profile = "ro-crate-1.3"
    rich.print(f"[b]{name}[/b]: validating {profile}…")
    validation = sh.Command("rocrate-validator")(
        "validate",
        "-p",
        profile,
        str(destination),
        _out=sys.stdout,
        _err=sys.stderr,
        _ok_code=PROCESS_EXIT_CODES,
        _return_cmd=True,
    )
    rich.print(f"[b]{name}[/b]: saved {destination.name}")
    return validation.exit_code != 0
