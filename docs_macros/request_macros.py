"""Render current and recorded requests for embedded examples."""

import shlex
from pathlib import Path
from textwrap import indent

from docs_macros.catalog import catalog, definition
from docs_macros.definitions import ContextExample, plain_title
from docs_macros.endpoints import default_endpoint, endpoint_url
from docs_macros.history import captures, selected_capture
from docs_macros.rendering.sources import source
from docs_macros.requests import saved_request, request_notice
from docs_macros.templates import render_jinja

ATTEMPT = "history_attempt"
ROOT_DIR = Path(__file__).resolve().parents[1]
JSONLD = "context.jsonld"
YAML = "context.yamlld"


def page_endpoint(environment, example):
    metadata = environment.page.meta
    if metadata.get(ATTEMPT):
        return selected_capture(example, metadata[ATTEMPT]).endpoint
    return metadata.get("history_endpoint") or default_endpoint(example)


class RequestMacros:
    """Request views using the current page's endpoint and attempt."""

    def retrieval_command(self, example, endpoint=None, query_file=None):
        settings = definition(example)
        address = endpoint_url(endpoint or page_endpoint(self.environment, example))
        attempt = self.environment.page.meta.get(ATTEMPT)
        if attempt:
            capture = selected_capture(example, attempt, address)
            saved = saved_request(capture, settings)
            if saved is None:
                return "# Inspect the recorded query and request metadata below."
            settings = saved
        return settings.command(address, query_file)

    def query_endpoint(self):
        return page_endpoint(self.environment, "eu-capitals")

    def query_text(self, example):
        attempt = self.environment.page.meta.get(ATTEMPT)
        if attempt:
            capture = selected_capture(
                example, attempt, page_endpoint(self.environment, example)
            )
            return (capture.directory / "query.rq").read_bytes().decode("utf-8")
        return definition(example).query

    def examples_index(self):
        return "\n\n".join(
            f"-   **[{settings.title}]({name}.md)**"
            for name, settings in catalog().items()
            if not isinstance(settings, ContextExample)
        )

    def context_examples_index(self):
        return "\n\n".join(
            _context_card(name, settings)
            for name, settings in catalog().items()
            if isinstance(settings, ContextExample)
        )

    def context_retrieval(self, example):
        settings = definition(example)
        saved = selected_capture(
            example,
            self.environment.page.meta.get(ATTEMPT),
            page_endpoint(self.environment, example),
        )
        repo_url = self.environment.conf["repo_url"]
        return "\n".join(
            _context_tab(
                {
                    "url": saved.endpoint or settings.url,
                    "name": settings.name,
                    "directory": saved.directory,
                    "filename": filename,
                    "flag": flag,
                    "repo_url": repo_url,
                }
            )
            for filename, flag in ((JSONLD, None), (YAML, "yamlld"))
        )

    def capture_notice(self, example):
        if self.environment.page.meta.get(ATTEMPT):
            return ""
        address = page_endpoint(self.environment, example)
        if not captures(example, address):
            return ""
        notice = request_notice(
            selected_capture(example, endpoint=address), definition(example)
        )
        return f'!!! info "Saved capture"\n\n    {notice}\n' if notice else ""


def _context_card(name, settings):
    return render_jinja(
        "context-card.md.j2",
        title=plain_title(settings.title),
        name=name,
        url=settings.url,
    )


def _context_tab(spec):
    mode = spec["flag"]
    label = "JSON-LD" if mode is None else "YAML-LD"
    body = _context_section(spec)
    return f'=== "{label}"\n\n{indent(body, "    ")}'


def _context_section(spec):
    mode = spec["flag"]
    relative = (spec["directory"] / spec["filename"]).relative_to(ROOT_DIR).as_posix()
    extension = "jsonld" if mode is None else "yamlld"
    document = source(relative, spec["repo_url"], title=spec["filename"])
    return render_jinja(
        "context-command.md.j2",
        url=shlex.quote(spec["url"]),
        serialization=mode,
        name=spec["name"],
        extension=extension,
        document=document,
    )
