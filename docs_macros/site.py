"""Build navigation and saved-attempt pages from executable definitions."""

import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from docs_macros.catalog import catalog, configure_catalog
from docs_macros.definitions import plain_title
from docs_macros.endpoints import endpoint_key
from docs_macros.history import captures, endpoints
from docs_macros.pages import generated_files, example_template
from docs_macros.lifecycle import on_build_error as on_build_error


def on_config(config):
    """Discover pages before MkDocs creates navigation and renders macros."""
    definitions = configure_catalog(Path(config.docs_dir))
    for entry in config.nav:
        if isinstance(entry, dict) and "Examples" in entry:
            entry["Examples"] = _navigation(entry["Examples"], definitions)
    return config


def _navigation(existing, definitions):
    supporting = [page for page in existing if not _executable_nav(page, definitions)]
    executable = [
        {plain_title(settings.title): f"examples/{name}.md"}
        for name, settings in definitions.items()
    ]
    return [supporting[0], *executable, *supporting[1:]]


def _executable_nav(page, definitions):
    if isinstance(page, dict):
        page = next(iter(page.values()))
    path = page
    name = path.removeprefix("examples/").removesuffix(".md")
    return name in definitions


def on_files(files, config):
    """Add shared layouts, endpoint views, and permanent capture views."""
    pages = {name: name for name in catalog()}
    pages["query-from-file"] = "eu-capitals"
    for page, example in pages.items():
        original = files.get_file_from_path(f"examples/{page}.md")
        if original is None:
            continue
        template = original.content_string
        if page in catalog():
            template = example_template(template, example)
            original.content_string = template
        _append_variants(files, page, example, template, config)
    return files


def _variants(example):
    variants = []
    for endpoint in endpoints(example):
        variants.append((f"{endpoint_key(endpoint)}.md", endpoint, None))
    for capture in captures(example):
        variants.append(
            (f"{capture.identifier}.md", capture.endpoint, capture.identifier)
        )
        if capture.endpoint:
            route = endpoint_key(capture.endpoint)
            variants.append(
                (
                    f"{route}/{capture.identifier}.md",
                    capture.endpoint,
                    capture.identifier,
                )
            )
    return variants


def on_nav(nav, config, files):
    """Keep generated views in their canonical page's navigation section."""
    for page_file in files:
        if not page_file.page:
            continue
        for name in (*catalog(), "query-from-file"):
            if page_file.src_uri.startswith(f"examples/{name}/"):
                canonical = files.get_file_from_path(f"examples/{name}.md")
                page_file.page.parent = canonical.page.parent
    return nav


def _append_variants(files, page, example, template, config):
    for generated in generated_files(
        page, example, template, _variants(example), config
    ):
        files.append(generated)
