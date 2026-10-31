"""Escape CSV cell text and link HTTP URLs to HTTPS destinations."""

import html
import re
from urllib.parse import urlsplit


def csv_cell(cell_text):
    pieces = []
    position = 0
    for match in re.finditer(r"https?://[^\s<>\"']+", cell_text):
        url = _trim_url(match.group())
        pieces.append(_escaped_prefix(cell_text, position, match.start()))
        pieces.append(_url_link(url))
        position = match.start()
        position += len(url)
    pieces.append(html.escape(cell_text[position:]))
    normalized = "".join(pieces).replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", "<br>")


def _trim_url(url):
    url = url.rstrip(".,;!")
    pairs = (("(", ")"), ("[", "]"), ("{", "}"))
    for opening, closing in pairs:
        while url.endswith(closing) and _unmatched_closing(url, opening, closing):
            url = url[:-1]
    return url


def _url_link(url):
    try:
        hostname = urlsplit(url).hostname
    except ValueError:
        hostname = None
    escaped = html.escape(url)
    if hostname:
        address = url.split("://", 1)[1]
        destination = html.escape(f"https://{address}")
        return f'<a href="{destination}" target="_blank" rel="noopener noreferrer">{escaped}</a>'
    return escaped


def _unmatched_closing(url, opening, closing):
    return url.count(closing) > url.count(opening)


def _escaped_prefix(cell_text, position, end):
    return html.escape(cell_text[position:end])
