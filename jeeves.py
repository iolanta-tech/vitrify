"""Project tasks for Vitrify. Run with `j <task>` (see https://jeeves.sh)."""

import sys
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import rich
import sh

from example_endpoints import ENDPOINTS, retrieval_command

PROFILE = "ro-crate-1.2"
PROJECT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = PROJECT_DIR / "docs" / "examples"

EXAMPLES = (
    ("female-persons", "retrieve.sh", "."),
    ("top-metaclasses", "retrieve.sh", "."),
    ("metaclasses-of-metaclasses", "retrieve.sh", "."),
    ("fourth-order-classes", "retrieve.sh", "."),
    ("select-turtle", "retrieve.sh", "."),
    ("time-bounded-subclasses", "retrieve.sh", "."),
    ("basic-example", "input/retrieve.sh", "eu-capitals"),
)


def examples() -> None:
    """Append one retrieval per endpoint for every example and validate each crate."""
    failed = False
    for name, script_path, crate_path in EXAMPLES:
        for endpoint in ENDPOINTS:
            directory = EXAMPLES_DIR / name
            rich.print(f"[b]{name}[/b]: running {ENDPOINTS[endpoint][0]} retrieval…")
            # Resolve the binary before changing directories; prefer this checkout's build.
            local_binary = PROJECT_DIR / "target" / "debug" / "vitrify"
            environment = os.environ.copy()
            if local_binary.is_file():
                environment["PATH"] = str(local_binary.parent) + os.pathsep + environment.get("PATH", "")
            with tempfile.TemporaryDirectory(prefix="vitrify-example-") as temporary:
                working_directory = Path(temporary)
                output = working_directory / (crate_path if crate_path != "." else name)
                completed = sh.Command("sh")(
                    "-c", retrieval_command(name, endpoint, directory),
                    _cwd=str(working_directory), _env=environment,
                    _out=sys.stdout, _err=sys.stderr, _ok_code=range(-128, 256), _return_cmd=True,
                )
                failed |= completed.exit_code != 0
                if not (output / "ro-crate-metadata.json").is_file():
                    rich.print(f"[red]{name}: no retrieval metadata was saved[/red]")
                    failed = True
                    continue
                while True:
                    identifier = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S%fZ")
                    destination = directory / identifier
                    try:
                        destination.mkdir()
                        break
                    except FileExistsError:
                        continue
                # Only Vitrify's generated output survives the temporary working directory.
                with tempfile.TemporaryDirectory(prefix=".pending-", dir=directory) as staging:
                    shutil.copytree(output, staging, dirs_exist_ok=True)
                    os.replace(staging, destination)
            rich.print(f"[b]{name}[/b]: validating {PROFILE}…")
            validation = sh.Command("rocrate-validator")(
                "validate", "-p", PROFILE, str(destination),
                _out=sys.stdout, _err=sys.stderr, _ok_code=range(-128, 256), _return_cmd=True,
            )
            failed |= validation.exit_code != 0
            rich.print(f"[b]{name}[/b]: saved {identifier}")
    if failed:
        raise SystemExit(1)


def serve() -> None:
    """Serve the Vitrify docs at http://localhost:6453."""
    sh.mkdocs.serve(
        "-a",
        "localhost:6453",
        _fg=True,
    )
