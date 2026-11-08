"""Build navigation and saved-attempt pages from executable definitions."""

import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY))

from docs_macros.catalog import catalog, configure_catalog
from docs_macros.definitions import ContextExample
from docs_macros.endpoints import endpoint_key
from docs_macros.history import captures, endpoints
from docs_macros.lifecycle import on_build_error as on_build_error
from docs_macros.navigation import navigation
from docs_macros.pages import example_template, generated_files


def on_config(config):
    """Discover pages before MkDocs creates navigation and renders macros."""
    definitions = configure_catalog(Path(config.docs_dir))
    for entry in config.nav:
        if isinstance(entry, dict) and "Examples" in entry:
            entry["Examples"] = navigation(entry["Examples"], definitions)
    return config


def on_files(files, config):
    """Add shared layouts, endpoint views, and permanent capture views."""
    pages = {name: name for name in catalog()}
    pages["query-from-file"] = "eu-capitals"
    for page, example in pages.items():
        _render_page(files, page, example, config)
    return files


def _render_page(files, page, example, config):
    original = files.get_file_from_path(f"examples/{page}.md")
    if original is None:
        return
    template = _template(original, page, example)
    if template is None:
        return
    _append_variants(files, page, example, template, config)


def _template(original, page, example):
    template = original.content_string
    if page not in catalog():
        return template
    if isinstance(catalog()[page], ContextExample):
        return None
    rendered = example_template(template, example)
    original.content_string = rendered
    return rendered


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
