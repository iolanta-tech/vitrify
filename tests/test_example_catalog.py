"""Exercise real Markdown-LD loading and automatic example registration."""

import pytest
import sh

from mkdocs.config import load_config
from mkdocs.structure.files import File, Files

from docs_macros import catalog as example_catalog
from docs_macros import history as example_history
from docs_macros import site as example_site
from docs_macros.definitions import Example

import catalog_fixtures
import fixture

REFERENCE = "Reference"
SPARQL = "SPARQL"
CONTEXT = "vitrify context"
OUTPUTS = "outputs/index.md"
CONTEXT_PAGE = "context/index.md"
EXAMPLES = "Examples"
EXAMPLES_PAGE = "examples/index.md"
CONTEXT_EXAMPLES = "context/examples/index.md"


class CatalogTests(catalog_fixtures.CatalogFixture):
    def test_registered_context_and_implicit_identity(self):
        self.page(endpoints=[catalog_fixtures.ENDPOINT, "https://another.example/sparql", catalog_fixtures.ENDPOINT])
        settings = example_catalog.load_catalog(self.root)[catalog_fixtures.NEW_EXAMPLE]
        assert settings.query == catalog_fixtures.QUERY
        assert settings.format is None
        assert settings.endpoints == tuple(sorted({catalog_fixtures.ENDPOINT, "https://another.example/sparql"}))
        assert "--format" not in settings.arguments(catalog_fixtures.ENDPOINT)

    def test_migrated_definitions(self):
        definitions = example_catalog.load_catalog()
        migrated = {
            "female-persons",
            "time-bounded-subclasses",
            "select-turtle",
            "eu-capitals",
            "fourth-order-classes",
            "metaclasses-of-metaclasses",
            "top-metaclasses",
        }
        assert migrated <= definitions.keys()
        assert "query-from-file" not in definitions
        assert fixture.search(r"(?i)\bLIMIT\s+5\s*$", definitions["select-turtle"].query)
        for name in migrated - {"select-turtle"}:
            settings = definitions[name]
            assert fixture.search(r"(?i)\bLIMIT\s+\d+", settings.query) is None
            assert len(settings.endpoints) == 2

    def test_incomplete_definitions_fail(self):
        for metadata in (
            {"query": ""},
            {"endpoints": []},
            {"format": "unknown"},
            {"query": 42},
            {"endpoints": [42]},
            {"@context": {}},
            {"format": ["csv", "json"]},
        ):
            self.page(**metadata)
            with pytest.raises(ValueError, match=catalog_fixtures.SOURCE):
                example_catalog.load_catalog(self.root)

    def test_context_command_redirects_to_a_filename(self, monkeypatch):

        from docs_macros.request_macros import _context_section

        directory = (
            catalog_fixtures.ROOT
            / "docs/examples/web-annotation/2026-11-08T000000000000Z"
        )
        spec = {
            "url": "https://www.w3.org/ns/anno.jsonld",
            "name": "web-annotation",
            "directory": directory,
            "filename": "context.jsonld",
            "flag": None,
            "repo_url": "https://github.com/iolanta-tech/vitrify",
        }
        with monkeypatch.context() as context:
            context.setattr(
                "docs_macros.request_macros.source",
                fixture.RecordedCall("INCLUDED"),
            )
            text = _context_section(spec)
        command = text.split("```sh", 1)[1]
        command = command.split("```", 1)[0]
        assert ("> web-annotation.jsonld") in command
        assert "docs/" not in command

    def test_context_url_is_a_context_example(self):
        path = self.page(name="web-annotation")
        path.write_text(
            "---\n"
            '"@context": urn:vitrify:examples\n'
            "context: https://www.w3.org/ns/anno.jsonld\n"
            "---\n"
            "# Web Annotation\n"
        )
        settings = example_catalog.load_catalog(self.root)["web-annotation"]
        assert settings.url == "https://www.w3.org/ns/anno.jsonld"
        assert settings.endpoints == ()

    def test_missing_query_fails(self):
        path = self.page()
        path.write_text(
            '---\n"@context": urn:vitrify:examples\nendpoints: [https://example.org/sparql]\n---\n# Broken\n'
        )
        with pytest.raises(ValueError, match="query"):
            example_catalog.load_catalog(self.root)

    def test_multiple_definitions_fail(self):
        metadata = {"@graph": [{catalog_fixtures.QUERY_PROPERTY: "ASK {}", catalog_fixtures.ENDPOINTS: [catalog_fixtures.ENDPOINT]}]}
        self.page(**metadata)
        with pytest.raises(ValueError, match="one executable definition"):
            example_catalog.load_catalog(self.root)

class LoaderTests(catalog_fixtures.CatalogFixture):
    def test_loader_errors_fail(self):
        metadata = {"@context": "urn:missing:context"}
        self.page(**metadata)
        with pytest.raises(ValueError, match="new-example.md"):
            example_catalog.load_catalog(self.root)


class DiscoveryTests(catalog_fixtures.CatalogFixture):
    def test_command_query_bytes(self):
        for query in (catalog_fixtures.QUERY, catalog_fixtures.QUERY.rstrip("\n")):
            settings = Example("example", "Example", query, (catalog_fixtures.ENDPOINT,))
            command = settings.command(catalog_fixtures.ENDPOINT)
            command = command.split(" |\n", 1)[0]
            completed = sh.sh("-c", command, _decode=False, _return_cmd=True)
            assert completed.stdout == query.encode("utf-8")

    def test_new_page_registration(self):
        self.page()
        config = load_config(
            config_file=str(catalog_fixtures.ROOT / "mkdocs.yml"), docs_dir=str(self.root)
        )
        config.plugins._current_plugin = "example_site"
        sparql = {SPARQL: [{"Outputs": [OUTPUTS]}, {EXAMPLES: [EXAMPLES_PAGE]}]}
        context = {CONTEXT: [CONTEXT_PAGE, {EXAMPLES: [CONTEXT_EXAMPLES]}]}
        config.nav = [{REFERENCE: [sparql, context]}]
        example_site.on_config(config)
        reference = config.nav[0][REFERENCE]
        sparql = reference[0][SPARQL]
        registered = sparql[1][EXAMPLES]
        context = reference[1][CONTEXT]
        assert sparql[0] == {"Outputs": [OUTPUTS]}
        assert registered[0] == EXAMPLES_PAGE
        assert registered[1] == {"New example": catalog_fixtures.SOURCE}
        assert context[1][EXAMPLES] == [CONTEXT_EXAMPLES]

    def test_context_pages_are_grouped_in_navigation(self):
        config = self._grouped_config()
        reference = config.nav[0][REFERENCE]
        sparql = reference[0][SPARQL]
        registered = sparql[1][EXAMPLES]
        context = reference[1][CONTEXT]
        assert sparql[0] == OUTPUTS
        assert registered[:2] == [EXAMPLES_PAGE, {"New example": catalog_fixtures.SOURCE}]
        assert context[0] == CONTEXT_PAGE
        assert context[1][EXAMPLES][:2] == [
            CONTEXT_EXAMPLES,
            {"Annotation": "examples/annotation.md"},
        ]
        assert reference[2] == {"Add an example": "authoring.md"}

    def test_context_pages_skip_variant_files(self, monkeypatch):
        config = self._grouped_config()
        files = Files(
            [
                File(
                    catalog_fixtures.SOURCE,
                    str(self.root),
                    str(self.root / "site"),
                    True,
                )
            ]
        )
        with monkeypatch.context() as context:
            context.setattr(example_history, "EXAMPLES_DIR", self.root / "examples")
            example_site.on_files(files, config)
            assert "retrieval_command('new-example')" in files.get_file_from_path(catalog_fixtures.SOURCE).content_string
            assert len(files) == 2
            assert example_history.captures(catalog_fixtures.NEW_EXAMPLE) == []
        assert not (self.root / "examples" / catalog_fixtures.NEW_EXAMPLE).exists()

    def test_context_pages_include_history(self, monkeypatch):
        config = self._grouped_config()
        files, identifier, saved_root = _prepare_context_page(self.root)
        with monkeypatch.context() as patch:
            patch.setattr(example_history, "EXAMPLES_DIR", saved_root)
            example_site.on_files(files, config)
        _assert_context_history(files, identifier)

    def test_new_page_index(self):
        from docs_macros.request_macros import RequestMacros

        self.page()
        example_catalog.configure_catalog(self.root)
        assert "[New example](new-example.md)" in RequestMacros().examples_index()

    def _grouped_config(self):
        self.page()
        (self.root / "examples" / "annotation.md").write_text(
            "---\n"
            '"@context": urn:vitrify:examples\n'
            "context: https://www.w3.org/ns/anno.jsonld\n"
            "---\n"
            "# Annotation\n"
        )
        config = load_config(
            config_file=str(catalog_fixtures.ROOT / "mkdocs.yml"),
            docs_dir=str(self.root),
        )
        config.plugins._current_plugin = "example_site"
        config.nav = [
            {
                REFERENCE: [
                    {SPARQL: [OUTPUTS, {EXAMPLES: [EXAMPLES_PAGE]}]},
                    {CONTEXT: [CONTEXT_PAGE, {EXAMPLES: [CONTEXT_EXAMPLES]}]},
                    {"Add an example": "authoring.md"},
                ],
            },
        ]
        example_site.on_config(config)
        return config


def _prepare_context_page(root):
    identifier = "2026-11-08T145518000000Z"
    page_path = next(root.rglob("annotation.md"))
    saved = page_path.parent / page_path.stem / identifier
    saved.mkdir(parents=True)
    (saved / "context.jsonld").write_text(_context_body())
    macro = "\n{{ context_retrieval('annotation') }}\n"
    page_path.write_text(page_path.read_text() + macro)
    return _page_files(root, page_path), identifier, page_path.parent


def _page_files(root, page_path):
    source = str(root)
    destination = str(root / "site")
    relative = page_path.relative_to(root).as_posix()
    return Files(
        [
            File(catalog_fixtures.SOURCE, source, destination, True),
            File(relative, source, destination, True),
        ]
    )


def _context_body():
    return "".join(
        (
            '{"http://schema.org/contentUrl":{"@id":"https://www.w3.org/ns/anno.jsonld"},',
            '"http://schema.org/contentSize":{"@value":"12"},',
            '"@reverse":{"http://schema.org/result":{',
            '"http://schema.org/actionStatus":{',
            '"@id":"http://schema.org/CompletedActionStatus"},',
            '"http://schema.org/startTime":{"@value":"2026-11-08T14:55:18+00:00"},',
            '"http://schema.org/endTime":{"@value":"2026-11-08T14:55:19+00:00"}}}}',
        )
    )


def _assert_context_history(files, identifier):
    page = files.get_file_from_path("examples/annotation.md")
    dated_path = "examples/annotation/{0}.md".format(identifier)
    dated = files.get_file_from_path(dated_path)
    assert "history_chart('annotation')" in page.content_string
    assert "context_retrieval('annotation')" in page.content_string
    assert dated is not None
    assert "history_attempt: {0}\n".format(identifier) in dated.content_string
