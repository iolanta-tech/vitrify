"""Share the validated Markdown-LD example catalog across site renderers."""

from dataclasses import dataclass
from pathlib import Path

from docs_macros.definitions import plain_title
from docs_macros.discovery import discover, sources
from docs_macros.storage import EXAMPLES_DIR, page_name
from docs_macros.validation import validate_definition


@dataclass
class CatalogState:
    """The catalog selected for the current documentation build."""

    definitions: dict | None = None


state = CatalogState()


def catalog():
    return load_catalog() if state.definitions is None else state.definitions


def configure_catalog(directory=EXAMPLES_DIR.parent):
    state.definitions = load_catalog(directory)
    return state.definitions


def definition(example):
    return catalog()[page_name(example)]


def load_catalog(directory=EXAMPLES_DIR.parent):
    directory = Path(directory)
    grouped = discover(directory)
    definitions = []
    for path, source in sources(directory).items():
        definitions.append(validate_definition(path, source, grouped.get(path, {})))
    definitions = [settings for settings in definitions if settings is not None]
    definitions.sort(key=lambda settings: plain_title(settings.title).casefold())
    return {settings.name: settings for settings in definitions}
