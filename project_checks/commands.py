"""Run project tools and collect concurrent check results."""

import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sh

PROJECT_DIR = Path(__file__).resolve().parents[1]
EXIT_STATUS_LIMIT = 256


def run_command(command, *arguments, repository=PROJECT_DIR):
    completed = sh.Command(str(command))(
        *arguments,
        _cwd=str(repository),
        _out=sys.stdout,
        _err=sys.stderr,
        _in="",
        _ok_code=range(EXIT_STATUS_LIMIT),
        _return_cmd=True,
    )
    return completed.exit_code


def run_parallel(*checks):
    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        futures = [executor.submit(check) for check in checks]
        return _collect_results(futures)


def _collect_results(futures):
    statuses = []
    errors = []
    for future in futures:
        try:
            statuses.append(future.result())
        except Exception as error:
            errors.append(error)
    if errors:
        raise errors[0]
    return max(statuses)
