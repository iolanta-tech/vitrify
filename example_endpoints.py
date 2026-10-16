"""Endpoint variants share one query and requested output format."""

import re
from pathlib import Path
from types import MappingProxyType

ENDPOINTS = MappingProxyType(
    {
        "wdqs": ("WDQS", "https://query.wikidata.org/sparql"),
        "qlever": ("QLever", "https://qlever.dev/api/wikidata"),
    }
)
EXAMPLES_DIR = Path(__file__).parent / "docs" / "examples"


def default_endpoint(example):
    return "wdqs" if example == "basic-example" else "qlever"


def retrieval_command(example, endpoint, directory=None):
    script = "input/retrieve.sh" if example == "basic-example" else "retrieve.sh"
    command = ((directory or EXAMPLES_DIR / example) / script).read_text()
    endpoint_url = ENDPOINTS[endpoint][1]
    command, replacements = re.subn(
        r"(--endpoint\s+)\S+",
        lambda match: f"{match[1]}{endpoint_url}",
        command,
    )
    if replacements != 1:
        raise ValueError(f"Expected one endpoint in {example}/{script}")
    return command.rstrip()


def endpoint_key(url):
    return next(
        (key for key, (_, address) in ENDPOINTS.items() if address == url), None
    )
