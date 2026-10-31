"""Render navigation through saved retrieval attempts."""

import html

from mkdocs.utils import get_relative_url

from docs_macros.endpoints import default_endpoint, endpoint_key, endpoint_label
from docs_macros.history import captures, selected_capture, endpoints
from docs_macros.rendering import details, selection
from docs_macros.storage import page_name
from docs_macros.templates import render_template

BAR_HEIGHT = 80
MINIMUM_BAR_HEIGHT = 3


def history_chart(example, attempt=None, page_url="", endpoint=None):
    endpoint = endpoint or default_endpoint(example)
    saved = captures(example, endpoint)
    navigation = _endpoint_tabs(
        example, _page_name(example, page_url), page_url, endpoint
    )
    if not saved:
        return f"{navigation}<p>No saved retrievals for this endpoint yet.</p>"
    selected = selected_capture(example, attempt, endpoint)
    links = _attempts(
        saved,
        selected,
        f"examples/{_page_name(example, page_url)}/{endpoint_key(endpoint)}",
        page_url,
    )
    return render_template(
        "history-chart.html",
        navigation=navigation,
        selected_detail=selection.selected_detail(selected),
        links=links,
    ).rstrip("\n")


def _page_name(example, page_url):
    if page_url.startswith("examples/query-from-file/"):
        return "query-from-file"
    return page_name(example)


def _endpoint_tabs(example, page_name, page_url, endpoint):
    links = []
    for address in endpoints(example):
        label = html.escape(endpoint_label(address))
        destination = get_relative_url(
            f"examples/{page_name}/{endpoint_key(address)}/", page_url
        )
        selected = ' aria-current="page"' if address == endpoint else ""
        links.append(f'<a href="{destination}"{selected}>{label}</a>')
    return "".join(
        (
            '<nav class="example-endpoints" aria-label="Query endpoint">',
            *links,
            "</nav>",
        )
    )


def _attempts(saved, selected, page_path, page_url):
    maximum = max((capture.byte_size or 0 for capture in saved), default=0)
    return "".join(
        _attempt(capture, selected, maximum, page_path, page_url) for capture in saved
    )


def _attempt(capture, selected, maximum, page_path, page_url):
    selected_attribute = (
        ' aria-current="page"' if capture.identifier == selected.identifier else ""
    )
    detail = html.escape(details.capture_detail(capture), quote=True)
    destination = get_relative_url(f"{page_path}/{capture.identifier}/", page_url)
    duration = html.escape(details.duration_label(capture, "Unknown time"))
    state = capture.status.lower()
    if capture.byte_size is None:
        state = f"{state} history-unknown"
    return render_template(
        "history-attempt.html",
        state=state,
        destination=destination,
        detail=detail,
        selected_attribute=selected_attribute,
        graphic=_graphic(capture, maximum),
        duration=duration,
        date=_date(capture),
    ).rstrip("\n")


def _graphic(capture, maximum):
    if capture.byte_size is None:
        return (
            '<span class="history-unknown-marker" aria-hidden="true">'
            '<span class="history-question">?</span></span>'
        )
    height = MINIMUM_BAR_HEIGHT
    if maximum:
        height = max(MINIMUM_BAR_HEIGHT, BAR_HEIGHT * capture.byte_size / maximum)
    return f'<span class="history-bar" style="height:{height:.2f}px"></span>'


def _date(capture):
    date = capture.started.strftime("%d %b")
    return f'<span class="history-date">{date}</span>'
