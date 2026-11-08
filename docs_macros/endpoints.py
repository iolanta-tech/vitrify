"""Endpoint labels and stable routes for current and historical requests."""

import hashlib
from types import MappingProxyType

from docs_macros.catalog import definition
from docs_macros.definitions import ContextExample

ROUTE_HASH_LENGTH = 16
ENDPOINTS = MappingProxyType(
    {
        "wdqs": ("WDQS", "https://query.wikidata.org/sparql"),
        "qlever": ("QLever", "https://qlever.dev/api/wikidata"),
    }
)


def endpoint_url(endpoint):
    return ENDPOINTS[endpoint][1] if endpoint in ENDPOINTS else endpoint


def endpoint_key(url):
    if url is None:
        return None
    for key, (_, address) in ENDPOINTS.items():
        if address == url:
            return key
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:ROUTE_HASH_LENGTH]
    return f"endpoint-{digest}"


def endpoint_label(url):
    for label, address in ENDPOINTS.values():
        if address == url:
            return label
    return url


def default_endpoint(example):
    settings = definition(example)
    if isinstance(settings, ContextExample):
        return settings.url
    return settings.endpoints[0]


def retrieval_command(example, endpoint):
    return definition(example).command(endpoint_url(endpoint))
