"""Render CLI pages from the generated model and authored hints."""

from pathlib import Path

from docs_macros.cli_page import argument_table, command_cards
from docs_macros.query_files import load_query
from docs_macros.service import CatalogService

DOCS = Path(__file__).resolve().parents[1] / "docs"


class CliReferenceTests:
    def test_sparql_arguments_come_from_the_model(self):
        table = _table("cli-arguments.rq", "sparql")
        assert "SPARQL endpoint URL." in table
        assert ("`--query PATH` or `--query -`") in table
        assert "[RO-Crate](https://www.researchobject.org/ro-crate/)" in table
        assert "fallback filename extension." in table

    def test_context_arguments_come_from_the_model(self):
        table = _table("cli-arguments.rq", "context")
        assert "Absolute HTTP(S) URL of the context." in table
        assert ("`--as jsonld` or `--as yamlld`") in table
        assert ':material-star:{ title="Required" }' in table
        assert ':material-star-outline:{ title="Optional" }' in table

    def test_command_cards_come_from_the_model(self):
        cards = command_cards(_rows(load_query("cli-commands.rq")))
        assert "**[sparql](../sparql.md)**" in cards
        assert "**[context](../context/index.md)**" in cards
        assert cards.index("sparql") < cards.index("context")


def _table(name, command):
    query = load_query(name).replace("COMMAND", command)
    return argument_table(_rows(query))


def _rows(query):
    with CatalogService(DOCS) as service:
        payload = service.query(query)
    return [{name: row[name]["value"] for name in row} for row in payload]
