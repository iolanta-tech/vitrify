"""Render an ADR status banner from page frontmatter."""

from datetime import date as date_type

ADR_STATUS = {
    "draft": "Draft",
    "undecided": "Undecided",
    "decided": "Decided",
}
ADR_STATUS_ADMONITION = {
    "draft": "note",
    "undecided": "warning",
    "decided": "success",
}


def adr_metadata(date, status, prerequisite=None):
    """Return a one-line admonition for an ADR's status and date."""
    key = str(status).lower()
    label = ADR_STATUS.get(key, str(status).replace("_", " ").title())
    parts = [label]
    if date:
        parts.append(f":material-calendar-clock: {_human_date(date)}")
    prerequisite_part = _prerequisite(prerequisite)
    if prerequisite_part:
        parts.append(prerequisite_part)
    kind = ADR_STATUS_ADMONITION.get(key, "note")
    return f'!!! {kind} "{" · ".join(parts)}"\n'


def _human_date(value):
    parsed = date_type.fromisoformat(value) if isinstance(value, str) else value
    return f'{parsed.day} {parsed.strftime("%B %Y")}'


def _prerequisite(value):
    if not isinstance(value, dict):
        return ""
    title = value.get("title")
    url = value.get("url")
    if not title or not url:
        return ""
    return f"Depends on [{title}]({url})"
