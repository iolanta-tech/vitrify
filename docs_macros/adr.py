"""Render an ADR status banner from page frontmatter."""

from datetime import date as date_type
from types import MappingProxyType

ADR_STATUS = MappingProxyType(
    {
        "draft": "Draft",
        "undecided": "Undecided",
        "decided": "Decided",
    }
)
ADR_STATUS_ADMONITION = MappingProxyType(
    {
        "draft": "note",
        "undecided": "warning",
        "decided": "success",
    }
)


def adr_metadata(date, status, prerequisite=None):
    """Return a one-line admonition for an ADR's status and date."""
    key = str(status).lower()
    parts = [_label(status, key)]
    if date:
        parts.append(f":material-calendar-clock: {_human_date(date)}")
    prerequisite_part = _prerequisite(prerequisite)
    if prerequisite_part:
        parts.append(prerequisite_part)
    kind = ADR_STATUS_ADMONITION[key] if key in ADR_STATUS_ADMONITION else "note"
    title = " · ".join(parts)
    return f'!!! {kind} "{title}"\n'


def _label(status, key):
    label = ADR_STATUS.get(key)
    if label is not None:
        return label
    return str(status).replace("_", " ").title()


def _human_date(raw):
    parsed = date_type.fromisoformat(raw) if isinstance(raw, str) else raw
    return f"{parsed.day} {parsed.strftime('%B %Y')}"


def _prerequisite(entry):
    if not isinstance(entry, dict):
        return ""
    title = entry["title"] if "title" in entry else ""
    url = entry["url"] if "url" in entry else ""
    if not title or not url:
        return ""
    return f"Depends on [{title}]({url})"
