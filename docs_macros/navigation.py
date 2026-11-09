"""Attach example pages to the Examples section of each use case."""

from docs_macros.definitions import ContextExample, plain_title

EXAMPLES = "Examples"


def register_examples(entries, definitions):
    sparql, context = _groups(definitions)
    _attach(entries, {"SPARQL": sparql, "vitrify context": context}, None)


def _attach(entries, pages, parent):
    for entry in entries:
        if isinstance(entry, dict):
            _attach_section(entry, pages, parent)


def _attach_section(entry, pages, parent):
    for title, children in list(entry.items()):
        if not isinstance(children, list):
            continue
        owned = pages.get(parent) if title == EXAMPLES else None
        if owned is not None:
            _append_missing(children, owned)
        _attach(children, pages, title)


def _append_missing(children, pages):
    present = {path for path in map(_page_path, children) if path}
    children.extend(page for page in pages if _page_path(page) not in present)


def _groups(definitions):
    sparql = []
    context = []
    for name, settings in definitions.items():
        link = {plain_title(settings.title): f"examples/{name}.md"}
        if isinstance(settings, ContextExample):
            context.append(link)
        else:
            sparql.append(link)
    return sparql, context


def _page_path(page):
    if isinstance(page, str):
        return page
    child = next(iter(page.values()))
    if isinstance(child, str):
        return child
    return None
