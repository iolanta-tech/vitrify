"""Register the saved-example renderers with MkDocs."""

import sys
from pathlib import Path
from textwrap import indent

sys.path.insert(0, str(Path(__file__).parent.resolve()))

from example_endpoints import ENDPOINTS, default_endpoint, retrieval_command
from example_rendering.details import capture_detail as capture_detail
from example_rendering.directories import directory_preview
from example_rendering.files import file_tabs
from example_rendering.history import history_chart
from example_rendering.sources import source

MACROS = (
    "directory_preview",
    "history_chart",
    "retrieval_command",
    "query_endpoint",
    "file_tabs",
    "source",
)
ATTEMPT = "history_attempt"


def _endpoint(environment, example):
    return environment.page.meta.get("history_endpoint") or default_endpoint(example)


class ExampleMacros:
    """Bind renderers to the current MkDocs page and configuration."""

    def __init__(self, environment):
        self.environment = environment

    def directory_preview(self, example):
        return directory_preview(
            example,
            self.environment.page.meta.get(ATTEMPT),
            _endpoint(self.environment, example),
        )

    def history_chart(self, example):
        return history_chart(
            example,
            self.environment.page.meta.get(ATTEMPT),
            self.environment.page.url,
            _endpoint(self.environment, example),
        )

    def retrieval_command(self, example):
        return retrieval_command(example, _endpoint(self.environment, example))

    def query_endpoint(self):
        return ENDPOINTS[_endpoint(self.environment, "basic-example")][1]

    def file_tabs(self, example):
        return file_tabs(
            example,
            self.environment.conf["repo_url"],
            self.environment.page.meta.get(ATTEMPT),
            self.environment.page.file.src_uri,
            _endpoint(self.environment, example),
        )

    def source(self, path, title="Source", collapsed=False):
        return source(
            path, self.environment.conf["repo_url"], title=title, collapsed=collapsed
        )


def _add_indentation(text, spaces=0):
    indented = indent(text, " " * spaces)
    return f"\n{indented}\n"


def define_env(env):
    """Register documentation macros with mkdocs-macros-plugin."""
    bound = ExampleMacros(env)
    for name in MACROS:
        env.macro(getattr(bound, name), name)
    env.filter(_add_indentation, "add_indentation")
