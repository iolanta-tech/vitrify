"""Render navigation through saved retrieval attempts."""

import html

from mkdocs.utils import get_relative_url

from example_endpoints import ENDPOINTS, default_endpoint
from example_history import captures, selected_capture
from example_rendering import details, selection

BAR_HEIGHT = 80
MINIMUM_BAR_HEIGHT = 3


def history_chart(example, attempt=None, page_url="", endpoint=None):
    endpoint = endpoint or default_endpoint(example)
    saved = captures(example, endpoint)
    navigation = _endpoint_tabs(_page_name(example, page_url), page_url, endpoint)
    if not saved:
        return f"{navigation}<p>No saved retrievals for this endpoint yet.</p>"
    selected = selected_capture(example, attempt, endpoint)
    links = _attempts(
        saved,
        selected,
        f"examples/{_page_name(example, page_url)}/{endpoint}",
        page_url,
    )
    return (
        f"{navigation}{selection.selected_detail(selected)}"
        '<section class="example-history" aria-label="Retrieval history">'
        '<div class="history-heading"><span>Response bytes</span>'
        '<span class="history-controls"><button type="button" data-history-scroll="-1" aria-label="Earlier retrievals">←</button>'
        '<button type="button" data-history-scroll="1" aria-label="Later retrievals">→</button></span></div>'
        f'<nav class="history-chart" aria-label="Saved retrievals">{links}</nav></section>'
    )


def _page_name(example, page_url):
    if page_url.startswith("examples/query-from-file/"):
        return "query-from-file"
    return "eu-capitals" if example == "basic-example" else example


def _endpoint_tabs(page_name, page_url, endpoint):
    links = []
    for key, (label, _) in ENDPOINTS.items():
        destination = get_relative_url(f"examples/{page_name}/{key}/", page_url)
        selected = ' aria-current="page"' if key == endpoint else ""
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
    return (
        f'<a class="history-attempt history-{state}" href="{destination}"'
        f' aria-label="{detail}" title="{detail}" data-history-detail="{detail}"{selected_attribute}>'
        f'<span class="history-column">{_graphic(capture, maximum)}</span>'
        f'<span class="history-duration">{duration}</span>'
        f"{_date(capture)}</a>"
    )


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
