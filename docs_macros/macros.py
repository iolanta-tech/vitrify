"""Register the saved-example renderers with MkDocs."""

from textwrap import indent

from docs_macros.request_macros import RequestMacros, page_endpoint
from docs_macros.rendering.details import capture_detail as capture_detail
from docs_macros.rendering.directories import directory_preview
from docs_macros.rendering.files import file_tabs
from docs_macros.rendering.history import history_chart
from docs_macros.rendering.sources import source

MACROS = (
    "directory_preview",
    "history_chart",
    "retrieval_command",
    "query_endpoint",
    "query_text",
    "examples_index",
    "capture_notice",
    "file_tabs",
    "source",
)
ATTEMPT = "history_attempt"


class ExampleMacros(RequestMacros):
    """Bind renderers to the current MkDocs page and configuration."""

    def __init__(self, environment):
        self.environment = environment

    def directory_preview(self, example):
        return directory_preview(
            example,
            self.environment.page.meta.get(ATTEMPT),
            page_endpoint(self.environment, example),
        )

    def history_chart(self, example):
        if (
            self.environment.page.meta.get(ATTEMPT)
            and page_endpoint(self.environment, example) is None
        ):
            return "The endpoint was not recorded for this attempt."
        return history_chart(
            example,
            self.environment.page.meta.get(ATTEMPT),
            self.environment.page.url,
            page_endpoint(self.environment, example),
        )

    def file_tabs(self, example):
        return file_tabs(
            example,
            self.environment.conf["repo_url"],
            self.environment.page.meta.get(ATTEMPT),
            self.environment.page.file.src_uri,
            page_endpoint(self.environment, example),
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
