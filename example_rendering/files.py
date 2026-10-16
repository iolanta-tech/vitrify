"""Render crate directories and artifact preview tabs."""

import html
from textwrap import indent

from mkdocs.utils import get_relative_url

from example_history import captures, selected_capture
from example_rendering import artifacts, tables

PREVIEW_ROWS = 5
PREVIEW_ERRORS = (ValueError, KeyError, TypeError)


def file_tabs(example, repo_url, attempt=None, page_url="", endpoint=None):
    if not captures(example, endpoint):
        return ""
    capture = selected_capture(example, attempt, endpoint)
    files = artifacts.crate_files(capture.directory)
    anchors = [
        f'<span id="{artifacts.anchor_id(file_path.name)}" '
        f'data-tab-target="{artifacts.tab_input_id(file_path.name)}"></span>'
        for file_path in files
    ]
    tabs = [_tab(capture, file_path, repo_url, page_url) for file_path in files]
    anchors = "\n\n".join(anchors)
    tabs = "".join(tabs)
    return f"{_notice(capture)}{anchors}\n\n{tabs}"


def _tab(capture, file_path, repo_url, page_url):
    repository_path = file_path.relative_to(artifacts.ROOT_DIR).as_posix()
    github_url = f"{repo_url.rstrip('/')}/blob/main/{repository_path}"
    documentation_path = file_path.relative_to(artifacts.ROOT_DIR / "docs").as_posix()
    download = get_relative_url(documentation_path, page_url)
    return (
        f'=== "{file_path.name}"\n\n{_preview(capture, file_path)}'
        f"\n    [Download `{file_path.name}`]({download}){{ .md-button }}\n"
        f"\n    [:fontawesome-brands-github: `{file_path.name}`]({github_url})"
        f"{{ .md-button .github-file-link }}\n\n"
    )


def _preview(capture, file_path):
    file_text = file_path.read_text(errors="replace")
    if file_path.name == "query.rq":
        return artifacts.code_block(file_text, "sparql")
    if file_path.name == artifacts.METADATA:
        return artifacts.code_block(file_text, artifacts.JSON_SYNTAX)
    if capture.status == "Success":
        return _result_preview(file_text, file_path)
    return artifacts.code_block(file_text, artifacts.PLAIN_TEXT)


def _result_preview(file_text, file_path):
    media_type = artifacts.file_media_type(file_path.parent, file_path.name)
    try:
        return _parsed_result(file_text, file_path, media_type)
    except PREVIEW_ERRORS:
        return artifacts.code_block(file_text, artifacts.PLAIN_TEXT)
    except tables.ElementTree.ParseError:
        return artifacts.code_block(file_text, artifacts.PLAIN_TEXT)


def _parsed_result(file_text, file_path, media_type):
    if media_type == "text/csv":
        return _indented_table(tables.csv_table(file_text))
    parser = {
        "application/sparql-results+json": tables.sparql_json,
        "application/sparql-results+xml": tables.sparql_xml,
    }.get(media_type)
    if parser:
        rows, headers = parser(file_text)
        return tables.table_preview(rows, headers, PREVIEW_ROWS)
    return artifacts.code_block(file_text, artifacts.syntax_for(file_path))


def _notice(capture):
    if capture.status == "Success":
        return ""
    message = (
        capture.error or "This retrieval did not finish. Its output may be incomplete."
    )
    escaped = indent(html.escape(message), artifacts.INDENTATION)
    return f'!!! failure "{capture.status}"\n\n{escaped}\n\n'


def _indented_table(table):
    indented = indent(table.rstrip("\n"), artifacts.INDENTATION)
    return f"{indented}\n"
