"""Group example pages in the documentation navigation."""

from docs_macros.definitions import ContextExample, plain_title

GUIDE = "query-from-file.md"


def navigation(existing, definitions):
    supporting = [
        page for page in existing if not _executable_nav(page, definitions)
    ]
    sparql, context = _groups(definitions)
    return _sections(supporting, sparql, context)


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


def _sections(supporting, sparql, context):
    sections = [supporting[0]]
    guides = supporting[1:]
    sparql_pages = [
        *sparql,
        *[page for page in guides if _page_path(page).endswith(GUIDE)],
    ]
    if sparql_pages:
        sections.append({"SPARQL": sparql_pages})
    if context:
        sections.append({"Context": context})
    sections.extend(
        page for page in guides if not _page_path(page).endswith(GUIDE)
    )
    return sections


def _page_path(page):
    if isinstance(page, dict):
        return next(iter(page.values()))
    return page


def _executable_nav(page, definitions):
    if isinstance(page, dict):
        page = next(iter(page.values()))
    name = page.removeprefix("examples/").removesuffix(".md")
    return name in definitions
