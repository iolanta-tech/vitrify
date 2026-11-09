"""Prepare canonical and dated example layouts before macro expansion."""

import re
from functools import partial

from mkdocs.structure.files import File, InclusionLevel

from docs_macros.templates import render_template


def example_template(source, example):
    layout = render_template("example.md", example=example)
    return f"{source.rstrip()}\n\n{layout}"


def context_template(source, example):
    chart = "{{{{ history_chart('{0}') }}}}".format(example)
    retrieval = "{{{{ context_retrieval('{0}') }}}}".format(example)
    if "history_chart(" in source:
        return source
    if retrieval in source:
        return source.replace(retrieval, "{0}\n\n{1}".format(chart, retrieval), 1)
    return "{0}\n\n{1}\n".format(source.rstrip(), chart)


def render_page(template, path, endpoint, identifier):
    depth = path.count("/") + 1
    adjusted = re.sub(
        r"(\]\()(?!(?:[a-z]+:|/|#))([^\s)]+)",
        partial(_relative_link, depth=depth),
        template,
    )
    address = endpoint or ""
    metadata = f"history_endpoint: {address}\n"
    if identifier:
        metadata = f"{metadata}history_attempt: {identifier}\n"
    return adjusted.replace("---\n", f"---\n{metadata}", 1)


def _relative_link(match, depth):
    prefix = "../" * depth
    return f"{match[1]}{prefix}{match[2]}"


def generated_files(page, example, template, variants, config):
    for path, endpoint, identifier in variants:
        yield File.generated(
            config,
            f"examples/{page}/{path}",
            content=render_page(template, path, endpoint, identifier),
            inclusion=InclusionLevel.NOT_IN_NAV,
        )
