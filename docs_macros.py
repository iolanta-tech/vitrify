"""Macros for rendering Vitrify's saved examples in MkDocs."""

import csv
import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from textwrap import indent


ROOT_DIR = Path(__file__).parent.resolve()
EXAMPLES_DIR = ROOT_DIR / "docs" / "examples"
PREVIEW_ROWS = 5
RO_CRATE_URL = "https://www.researchobject.org/ro-crate/"


def directory_preview(example, link_prefix="examples/"):
    """Render only the generated crate contents as a directory tree."""
    example_dir = _example_directory(example)
    crate_dir = _crate_directory(example_dir)
    result_entity = _result_entity(crate_dir)
    media_type = result_entity["encodingFormat"]

    if media_type == "text/csv":
        result_icon = "material-table"
    elif "json" in media_type:
        result_icon = "material-code-json"
    elif media_type == "text/turtle":
        result_icon = "material-code-braces"
    else:
        result_icon = "material-file-document-outline"

    result_name = result_entity["@id"]
    link_root = "/".join(
        part.strip("/") for part in (link_prefix, example) if part.strip("/")
    )
    link_root = f"/{link_root}"
    crate_relative_path = crate_dir.relative_to(example_dir)
    if crate_relative_path == Path("."):
        crate_link_root = link_root
        crate_name = example
    else:
        crate_link_root = f"{link_root}/{crate_relative_path.as_posix()}"
        crate_name = crate_relative_path.name
    lines = [f":material-folder-open: `{crate_name}/`  "]
    entries = (
        ("material-file-document-outline", "query.rq"),
        (result_icon, result_name),
        ("material-code-json", "ro-crate-metadata.json"),
    )
    for index, (icon, name) in enumerate(entries):
        branch = "└──" if index == len(entries) - 1 else "├──"
        lines.append(
            f"{branch} :{icon}: [`{name}`]({crate_link_root}/{name})  "
        )
    return "\n".join(lines)


def response_table(example, link_prefix="examples/"):
    """Render a short table derived from an example's saved response."""
    example_dir = _example_directory(example)
    crate_dir = _crate_directory(example_dir)
    result_entity = _result_entity(crate_dir)
    result_path = crate_dir / result_entity["@id"]
    result_url = "/".join(
        part.strip("/")
        for part in (
            link_prefix,
            example,
            result_path.relative_to(example_dir).as_posix(),
        )
    )
    result_url = f"/{result_url}"
    content = result_path.read_text()

    if "json" in result_entity["encodingFormat"]:
        rows, headers = _sparql_json(content)
    elif "csv" in result_entity["encodingFormat"]:
        rows, headers = _csv(content)
    elif "xml" in result_entity["encodingFormat"]:
        rows, headers = _sparql_xml(content)
    else:
        raise ValueError(f"Cannot render a tabular preview for {result_path}")

    preview = rows[:PREVIEW_ROWS]
    table = [
        f"Showing {len(preview)} of {len(rows)} rows from the "
        f"[captured response]({result_url}):",
        "",
        "| " + " | ".join(_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    table.extend(
        "| " + " | ".join(_cell(value) for value in row) + " |"
        for row in preview
    )
    return "\n".join(table)


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
    env.macro(response_table)
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


def _csv(content):
    reader = csv.reader(content.splitlines())
    headers = next(reader)
    return list(reader), headers


def _cell(value):
    return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ")
