"""Write the CLI documentation model from the built vitrify binary."""

import sys
from pathlib import Path

import sh

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "docs/cli/model.yamlld"


def cli_model(check: bool = False) -> None:
    """Write docs/cli/model.yamlld from the vitrify CLI.

    --check fails when the committed model differs.
    """
    generated = _generate()
    if check and generated != MODEL.read_text(encoding="utf-8"):
        sys.stderr.write("CLI model is stale. Run j cli-model.\n")
        sys.exit(1)
    if not check:
        MODEL.write_text(generated, encoding="utf-8")


def _generate():
    return str(sh.cargo("run", "-q", "--", "cli-model", _cwd=str(ROOT)))
