"""Reload the build dataset after a failed documentation render."""

from mkdocs_macros_sparqld import run_query, stop_server
from mkdocs_macros_sparqld.render import parse_result
from mkdocs_macros_sparqld.server import configure

from docs_macros.site import on_build_error
from catalog_fixtures import CatalogFixture

ASK_CAPTURE = "ASK { <urn:capture> <urn:status> <urn:saved> }"


class BuildRecoveryTests(CatalogFixture):
    def test_failed_build_reloads_dataset(self):
        configure(project_dir=self.root, directory=self.root, binary="sparqld")
        self.add_cleanup(stop_server)
        assert not parse_result(*run_query(ASK_CAPTURE))
        (self.root / "capture.ttl").write_text(
            "<urn:capture> <urn:status> <urn:saved> .\n"
        )
        assert not parse_result(*run_query(ASK_CAPTURE))
        on_build_error(RuntimeError("render failed"))
        assert parse_result(*run_query(ASK_CAPTURE))
