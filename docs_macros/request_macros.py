"""Render current and recorded requests for embedded examples."""

from docs_macros.catalog import catalog, definition
from docs_macros.endpoints import default_endpoint, endpoint_url
from docs_macros.history import captures, selected_capture
from docs_macros.requests import saved_request, request_notice

ATTEMPT = "history_attempt"


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
