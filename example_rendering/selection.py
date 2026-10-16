"""Render the selected retrieval's timestamp, outcome, and measurements."""

import html
from types import MappingProxyType

from example_rendering import details

STATUS_ICONS = MappingProxyType(
    {
        "Success": "check-circle",
        "Failure": "close-circle",
        "Incomplete": "progress-clock",
    }
)


def selected_detail(capture):
    fields = [_time_field(capture), _status_field(capture), _duration_field(capture)]
    if capture.byte_size is not None:
        fields.append(f"<span>{details.byte_label(capture.byte_size)}</span>")
    separator = '<span class="history-separator" aria-hidden="true">·</span>'
    return f'<p class="history-detail" aria-label="Selected retrieval">{separator.join(fields)}</p>'


def _time_field(capture):
    timestamp = capture.started.strftime("%d %b %Y, %H:%M:%S UTC")
    machine_time = capture.started.isoformat()
    return f'<span>{details.icon("calendar")}<time datetime="{machine_time}">{timestamp}</time></span>'


def _status_field(capture):
    status_icon = details.icon(STATUS_ICONS[capture.status])
    state = capture.status.lower()
    return f'<span class="history-outcome history-outcome-{state}">{status_icon}{capture.status}</span>'


def _duration_field(capture):
    title = (
        "Estimated retrieval duration"
        if capture.estimated_duration
        else "Retrieval duration"
    )
    duration = html.escape(details.duration_label(capture))
    suffix = " duration" if capture.duration is None else ""
    return f'<span title="{title}">{details.icon("timer-outline")}{duration}{suffix}</span>'
