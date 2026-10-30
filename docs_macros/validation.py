"""Validate RDF execution definitions before constructing requests."""

from urllib.parse import urlsplit

from docs_macros.definitions import Example, FORMATS, heading

CONTEXT = "urn:vitrify:examples"
BINDING = "value"
STRING = "http://www.w3.org/2001/XMLSchema#string"


def validate_definition(path, source, subjects):
    if not _candidate(source[1], subjects):
        return None
    if len(subjects) != 1:
        raise ValueError(f"{path}: expected one executable definition")
    properties = next(iter(subjects.values()))
    return Example(
        name=path.removeprefix("examples/").removesuffix(".md"),
        title=heading(source[0]),
        query=_literal(properties, "query", path),
        endpoints=_endpoints(properties, path),
        format=_format(properties, path),
    )


def _candidate(metadata, subjects):
    if subjects or metadata.get("@context") == CONTEXT:
        return True
    return any(key in metadata for key in ("query", "endpoints"))


def _endpoints(properties, path):
    bindings = properties.get("endpoints", [])
    if not bindings or not all(_http_iri(binding) for binding in bindings):
        raise ValueError(f"{path}: endpoints must contain HTTP(S) IRIs")
    return tuple(sorted({binding[BINDING] for binding in bindings}))


def _http_iri(binding):
    address = urlsplit(binding[BINDING])
    return (
        binding["type"] == "uri"
        and address.scheme in {"http", "https"}
        and bool(address.netloc)
    )


def _format(properties, path):
    requested = _literal(properties, "format", path, optional=True)
    if requested is not None and requested not in FORMATS:
        raise ValueError(f"{path}: unsupported format {requested!r}")
    return requested


def _literal(properties, name, path, optional=False):
    bindings = properties.get(name, [])
    if optional and not bindings:
        return None
    if len(bindings) != 1 or not _string(bindings[0]):
        raise ValueError(f"{path}: {name} must be one nonempty string")
    return bindings[0][BINDING]


def _string(binding):
    return (
        binding["type"] == "literal"
        and bool(binding[BINDING].strip())
        and binding.get("datatype", STRING) == STRING
        and "xml:lang" not in binding
    )
