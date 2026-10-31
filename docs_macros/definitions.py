"""Validated execution settings obtained from Markdown-LD source graphs."""

import re
import shlex
from dataclasses import dataclass
from types import MappingProxyType

BACKSLASH = r"\ "[0]
FORMATS = MappingProxyType(
    {
        "json": "application/sparql-results+json",
        "xml": "application/sparql-results+xml",
        "csv": "text/csv",
        "tsv": "text/tab-separated-values",
        "turtle": "text/turtle",
        "ntriples": "application/n-triples",
        "rdfxml": "application/rdf+xml",
        "jsonld": "application/ld+json",
    }
)


@dataclass(frozen=True)
class Example:
    """One page and its future retrieval requests."""

    name: str
    title: str
    query: str
    endpoints: tuple[str, ...]
    format: str | None = None

    def arguments(self, endpoint, output=None, query="-"):
        arguments = ["sparql", "--endpoint", endpoint, "--query", query]
        if self.format is not None:
            arguments.extend(("--format", self.format))
        return [*arguments, "--to", str(output or self.name)]

    def command(self, endpoint, query_file=None):
        arguments = self.arguments(endpoint, query=query_file or "-")
        flags = arguments[1::2]
        pairs = zip(flags, arguments[2::2], strict=True)
        separator = f" {BACKSLASH}\n  "
        invocation = "vitrify sparql {arguments}".format(
            arguments=separator.join(shlex.join(pair) for pair in pairs)
        )
        if query_file:
            return invocation
        # printf preserves query bytes, including a missing final newline.
        return f"printf '%s' {shlex.quote(self.query)} |\n  {invocation}"


def heading(source):
    match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
    if match is None:
        raise ValueError("Example requires a Markdown heading")
    return match[1]


def plain_title(title):
    return re.sub(r":[a-z][a-z0-9_-]*:\s*", "", title)
