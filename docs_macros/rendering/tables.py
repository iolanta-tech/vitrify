"""Render saved tabular results as HTML or Markdown."""

import csv
import html
import io
import json
from xml.etree import ElementTree

from docs_macros.rendering.links import csv_cell

NAMESPACE = "{http://www.w3.org/2005/sparql-results#}"


def table_preview(rows, headers, limit=None):
    preview = rows if limit is None else rows[:limit]
    lines = []
    if len(preview) < len(rows):
        notice = f"Showing {len(preview)} of {len(rows)} rows."
        lines.extend((notice, ""))
    separators = _markdown_row(("---" for _ in headers))
    lines.extend((_markdown_row(headers), separators))
    lines.extend(_markdown_row(row) for row in preview)
    body = "\n    ".join(lines)
    return f"    {body}\n"


def _markdown_row(cells):
    escaped = (
        html.escape(str(cell)).replace("|", "&#124;").replace("\n", " ")
        for cell in cells
    )
    cells_text = " | ".join(escaped)
    return f"| {cells_text} |"


def csv_table(csv_text, limit=None):
    rows = csv.reader(io.StringIO(csv_text, newline=""))
    headers = next(rows, None)
    if headers is None:
        return ""
    rows = list(rows)
    preview = rows if limit is None else rows[:limit]
    body = "\n".join(_html_row(row, "td") for row in preview)
    notice = (
        f"<p>Showing {len(preview)} of {len(rows)} rows.</p>"
        if len(preview) < len(rows)
        else ""
    )
    return f"{notice}<table>\n<thead>{_html_row(headers, 'th')}</thead>\n<tbody>\n{body}\n</tbody>\n</table>"


def _html_row(row_cells, tag):
    escaped = (csv_cell(cell_text) for cell_text in row_cells)
    wrapped = (f"<{tag}>{cell_text}</{tag}>" for cell_text in escaped)
    cells = "".join(wrapped)
    return f"<tr>{cells}</tr>"


def sparql_json(json_text):
    document = json.loads(json_text)
    headers = document["head"]["vars"]
    rows = [
        [binding.get(header, {}).get("value", "") for header in headers]
        for binding in document["results"]["bindings"]
    ]
    return rows, headers


def sparql_xml(xml_text):
    document = ElementTree.fromstring(xml_text)
    headers = [
        element.attrib["name"]
        for element in document.findall(f"{NAMESPACE}head/{NAMESPACE}variable")
    ]
    rows = []
    for element in document.findall(f"{NAMESPACE}results/{NAMESPACE}result"):
        rows.append(_xml_row(element, headers))
    return rows, headers


def _xml_row(element, headers):
    bindings = {
        binding.attrib["name"]: next(iter(binding), None)
        for binding in element.findall(f"{NAMESPACE}binding")
    }
    cells = (getattr(bindings.get(name), "text", "") for name in headers)
    return [cell or "" for cell in cells]
