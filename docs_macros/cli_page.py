"""Render CLI reference tables from the sparqld model."""

import re

from mkdocs_macros_sparqld import run_query
from mkdocs_macros_sparqld.render import parse_result

from docs_macros.query_files import load_query


def cli_arguments(command):
    return argument_table(_select("cli-arguments.rq", command))


def cli_commands():
    return command_cards(_select("cli-commands.rq"))


def argument_table(rows):
    lines = [
        "| Argument | Required | Description |",
        "| --- | :---: | --- |",
    ]
    lines.extend(_argument_row(row) for row in rows)
    return "\n".join(lines)


def command_cards(rows):
    return "\n\n".join(_card(row) for row in rows)


def _select(name, command=None):
    query = load_query(name)
    if command is not None:
        if re.fullmatch(r"[a-z]+", command) is None:
            raise ValueError(f"Invalid CLI command: {command}")
        query = query.replace("COMMAND", command)
    rows = parse_result(*run_query(query))
    if not isinstance(rows, list):
        raise ValueError(f"{name} must return rows")
    return rows


def _argument_row(row):
    escaped = r"\|"
    usage = " or ".join(
        f"`{part.replace('|', escaped)}`" for part in row["usage"].split(" or ")
    )
    description = row["description"].replace("|", escaped)
    required = {
        "true": ':material-star:{ title="Required" }',
        "false": ':material-star-outline:{ title="Optional" }',
    }[row["required"]]
    return f"| {usage} | {required} | {description} |"


def _card(row):
    name = row["name"]
    page = row["page"]
    icon = row["icon"]
    summary = row["summary"]
    return "\n".join(
        (
            f"-   :material-{icon}: **[{name}]({page})**",
            "",
            "    ---",
            "",
            f"    {summary} [:material-arrow-right:]({page})",
        )
    )
