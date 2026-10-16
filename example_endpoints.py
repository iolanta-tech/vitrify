"""Endpoint variants share one query and requested output format."""

import re
from pathlib import Path

ENDPOINTS = {
    "wdqs": ("WDQS", "https://query.wikidata.org/sparql"),
    "qlever": ("QLever", "https://qlever.dev/api/wikidata"),
}
EXAMPLES_DIR = Path(__file__).parent / "docs" / "examples"


def default_endpoint(example):
    return "wdqs" if example == "basic-example" else "qlever"


def retrieval_command(example, endpoint, directory=None):
    script = "input/retrieve.sh" if example == "basic-example" else "retrieve.sh"
    command = ((directory or EXAMPLES_DIR / example) / script).read_text()
    command, replacements = re.subn(r"(--endpoint\s+)\S+", lambda match: match[1] + ENDPOINTS[endpoint][1], command)
    if replacements != 1:
        raise ValueError(f"Expected one endpoint in {example}/{script}")
    return command.rstrip()
