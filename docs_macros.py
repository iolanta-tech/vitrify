"""Macros for rendering Vitrify's saved examples in MkDocs."""

import csv
import html
import io
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from textwrap import indent
from urllib.parse import urlsplit

from markdown.extensions.toc import slugify_unicode


ROOT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = ROOT_DIR / "docs" / "examples"
PREVIEW_ROWS = 5
RO_CRATE_URL = "https://www.researchobject.org/ro-crate/"


def directory_preview(example):
    """Render only the generated crate contents as a directory tree."""
    example_dir = _example_directory(example)
    crate_dir = _crate_directory(example_dir)
    crate_relative_path = crate_dir.relative_to(example_dir)
    crate_name = (
        example if crate_relative_path == Path(".") else crate_relative_path.name
    )
    lines = [f":material-folder-open: `{crate_name}/`  "]
    files = _crate_files(crate_dir)
    for index, file_path in enumerate(files):
        media_type = _file_media_type(crate_dir, file_path.name)
        icon = _file_icon(file_path.name, media_type)
        branch = "└──" if index == len(files) - 1 else "├──"
        lines.append(
            f"{branch} :{icon}: [`{file_path.name}`](#{_anchor_id(file_path.name)})  "
        )
    return "\n".join(lines)


def file_tabs(example, repo_url):
    """Render the crate files as filename tabs with GitHub source links."""
    example_dir = _example_directory(example)
    crate_dir = _crate_directory(example_dir)
    files = _crate_files(crate_dir)
    anchors = [
        f'<span id="{_anchor_id(file_path.name)}" '
        f'data-tab-target="{_tab_input_id(file_path.name)}"></span>'
        for file_path in files
    ]
    tabs = []
    for file_path in files:
        name = file_path.name
        repository_path = file_path.relative_to(ROOT_DIR).as_posix()
        github_url = f"{repo_url.rstrip('/')}/blob/main/{repository_path}"
        tabs.append(
            f'=== "{name}"\n\n'
        )
        content = file_path.read_text()
        if name == "query.rq":
            tabs.append(_code_block(content, "sparql"))
        elif name == "ro-crate-metadata.json":
            tabs.append(_code_block(content, "json"))
        else:
            media_type = _file_media_type(crate_dir, name)
            if media_type == "text/csv":
                tabs.append(_indented_table(_csv_table(content)))
            elif "json" in media_type:
                rows, headers = _sparql_json(content)
                tabs.append(_table_preview(rows, headers, PREVIEW_ROWS))
            elif "xml" in media_type:
                rows, headers = _sparql_xml(content)
                tabs.append(_table_preview(rows, headers, PREVIEW_ROWS))
            else:
                tabs.append(_code_block(content, _syntax_for(file_path)))
        tabs.append(
            f'\n    [:fontawesome-brands-github: `{name}`]({github_url})'
            f'{{ .md-button .github-file-link }}\n'
        )
        tabs.append("\n")
    return "\n\n".join(anchors) + "\n\n" + "\n".join(tabs)


def source(path, repo_url, title="Source", collapsed=False):
    """Render a project file in a code block linked to its GitHub source."""
    source_path = (ROOT_DIR / path).resolve()
    if not source_path.is_relative_to(ROOT_DIR):
        raise ValueError(f"Invalid source path: {path}")
    if not source_path.is_file():
        raise ValueError(f"Documentation source does not exist: {path}")

    if title.startswith("RO-Crate"):
        title = f"[RO-Crate]({RO_CRATE_URL}){title.removeprefix('RO-Crate')}"

    repository_path = Path(path).as_posix()
    github_url = f"{repo_url.rstrip('/')}/blob/main/{repository_path}"
    syntax = {".json": "json", ".rq": "sparql", ".sh": "bash"}.get(
        source_path.suffix.lower(),
        "text",
    )
    contents = source_path.read_text().rstrip("\n")
    heading = (
        f'{title}<span class="example-source-link" markdown>'
        f':fontawesome-brands-github: [`{source_path.name}`]({github_url})'
        "</span>"
    )
    code = f"```{syntax}\n{contents}\n```"
    marker = "???" if collapsed else "!!!"
    return f'{marker} example "{heading}"\n\n{indent(code, "    ")}\n'


def define_env(env):
    """Register documentation macros with mkdocs-macros-plugin."""
    env.macro(directory_preview)
    env.filter(
        lambda text, spaces=0: "\n" + indent(text, " " * spaces) + "\n",
        "add_indentation",
    )
    env.macro(
        lambda example: file_tabs(
            example,
            env.conf["repo_url"],
        ),
        "file_tabs",
    )
    env.macro(
        lambda path, title="Source", collapsed=False: source(
            path,
            env.conf["repo_url"],
            title=title,
            collapsed=collapsed,
        ),
        "source",
    )


def _example_directory(example):
    example_dir = (EXAMPLES_DIR / example).resolve()
    if not example_dir.is_relative_to(EXAMPLES_DIR):
        raise ValueError(f"Invalid example directory: {example}")
    if not example_dir.is_dir():
        raise ValueError(f"Example directory does not exist: {example}")
    return example_dir


def _result_entity(example_dir):
    metadata = json.loads((example_dir / "ro-crate-metadata.json").read_text())
    return next(
        entity
        for entity in metadata["@graph"]
        if entity.get("@type") == "File"
        and entity.get("@id", "").startswith("results.")
    )


def _crate_files(crate_dir):
    result_name = _result_entity(crate_dir)["@id"]
    return tuple(
        crate_dir / name
        for name in (result_name, "ro-crate-metadata.json", "query.rq")
    )


def _file_media_type(crate_dir, file_name):
    if file_name == "ro-crate-metadata.json":
        return "application/ld+json"
    entity = next(
        entity
        for entity in json.loads(
            (crate_dir / "ro-crate-metadata.json").read_text()
        )["@graph"]
        if entity.get("@type") == "File" and entity.get("@id") == file_name
    )
    return entity["encodingFormat"]


def _file_icon(file_name, media_type):
    if file_name == "query.rq":
        return "material-file-document-outline"
    if file_name == "ro-crate-metadata.json":
        return "material-code-json"
    if media_type == "text/csv":
        return "material-table"
    if "json" in media_type:
        return "material-code-json"
    if media_type == "text/turtle":
        return "material-code-braces"
    return "material-file-document-outline"


def _anchor_id(file_name):
    return slugify_unicode(f"file-{file_name}", "-")


def _tab_input_id(file_name):
    return slugify_unicode(file_name, "-")


def _syntax_for(path):
    return {
        ".json": "json",
        ".rq": "sparql",
        ".ttl": "turtle",
        ".xml": "xml",
    }.get(path.suffix.lower(), "text")


def _code_block(content, syntax):
    code = indent(content.rstrip("\n"), "    ")
    return f"    ```{syntax}\n{code}\n    ```\n"


def _table_preview(rows, headers, limit=None):
    preview = rows if limit is None else rows[:limit]
    lines = []
    if len(preview) < len(rows):
        lines.extend((f"Showing {len(preview)} of {len(rows)} rows.", ""))
    lines.extend(
        (
            "| " + " | ".join(_cell(header) for header in headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        )
    )
    lines.extend(
        "| " + " | ".join(_cell(value) for value in row) + " |"
        for row in preview
    )
    return "    " + "\n    ".join(lines) + "\n"


def _indented_table(table):
    return indent(table.rstrip("\n"), "    ") + "\n"


def _csv_table(content):
    """Render CSV headers and rows as an escaped HTML table."""
    rows = csv.reader(io.StringIO(content, newline=""))
    headers = next(rows, None)
    if headers is None:
        return ""

    def row(values, tag):
        cells = "".join(f"<{tag}>{_csv_cell(value)}</{tag}>" for value in values)
        return f"<tr>{cells}</tr>"

    return (
        "<table>\n<thead>" + row(headers, "th") + "</thead>\n<tbody>\n"
        + "\n".join(row(values, "td") for values in rows)
        + "\n</tbody>\n</table>"
    )


def _csv_cell(value):
    """Escape cell text and link HTTP(S) URLs with HTTPS destinations."""
    pieces = []
    position = 0
    for match in re.finditer(r"https?://[^\s<>\"']+", value):
        url = match.group().rstrip(".,;!")
        for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
            while url.endswith(closing) and url.count(closing) > url.count(opening):
                url = url[:-1]
        pieces.append(html.escape(value[position:match.start()]))
        escaped = html.escape(url)
        try:
            hostname = urlsplit(url).hostname
        except ValueError:
            hostname = None
        if hostname:
            destination = html.escape("https://" + url.split("://", 1)[1])
            pieces.append(
                f'<a href="{destination}" target="_blank" '
                f'rel="noopener noreferrer">{escaped}</a>'
            )
        else:
            pieces.append(escaped)
        position = match.start() + len(url)
    pieces.append(html.escape(value[position:]))
    return "".join(pieces).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def _crate_directory(example_dir):
    """Find the example's RO-Crate, whether nested or at its root."""
    if (example_dir / "ro-crate-metadata.json").is_file():
        return example_dir

    crate_directories = [
        path
        for path in example_dir.iterdir()
        if path.is_dir() and (path / "ro-crate-metadata.json").is_file()
    ]
    if len(crate_directories) == 1:
        return crate_directories[0]
    raise ValueError(f"Expected exactly one RO-Crate in {example_dir}")


def _sparql_json(content):
    document = json.loads(content)
    headers = document["head"]["vars"]
    bindings = document["results"]["bindings"]
    rows = [
        [binding.get(header, {}).get("value", "") for header in headers]
        for binding in bindings
    ]
    return rows, headers


def _sparql_xml(content):
    namespace = "{http://www.w3.org/2005/sparql-results#}"
    document = ET.fromstring(content)
    headers = [
        variable.attrib["name"]
        for variable in document.findall(f"{namespace}head/{namespace}variable")
    ]
    rows = []
    for result in document.findall(f"{namespace}results/{namespace}result"):
        bindings = {
            binding.attrib["name"]: next(iter(binding), None)
            for binding in result.findall(f"{namespace}binding")
        }
        rows.append(
            [
                bindings[name].text or "" if bindings.get(name) is not None else ""
                for name in headers
            ]
        )
    return rows, headers


def _cell(value):
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ")
