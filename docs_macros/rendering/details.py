"""Format retrieval measurements and selected-capture details."""

from importlib.resources import files

MINIMUM_DISPLAY_DURATION = 0.01


def duration_number(seconds):
    if 0 < seconds < MINIMUM_DISPLAY_DURATION:
        return "<0.01"
    return f"{seconds:.2f}"


def duration_label(capture, unknown="Unknown"):
    if capture.duration is None:
        return unknown
    prefix = "≈ " if capture.estimated_duration else ""
    return f"{prefix}{duration_number(capture.duration)} s"


def byte_label(size):
    if size is None:
        return "Byte count unavailable"
    unit = "byte" if size == 1 else "bytes"
    return f"{size:,} {unit}"


def capture_detail(capture):
    parts = [
        capture.started.strftime("%d %b %Y, %H:%M:%S UTC"),
        capture.status,
        byte_label(capture.byte_size),
    ]
    if capture.duration is None:
        parts.append("Duration unavailable")
    else:
        prefix = (
            "Estimated duration" if capture.estimated_duration else "Retrieval duration"
        )
        parts.append(f"{prefix}: {duration_number(capture.duration)} s")
    return " · ".join(parts)


def icon(name):
    svg = (
        files("material").joinpath(f"templates/.icons/material/{name}.svg").read_text()
    )
    return f'<span class="history-icon" aria-hidden="true">{svg}</span>'
