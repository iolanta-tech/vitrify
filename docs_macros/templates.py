"""Render documentation fragments stored beside the project sources."""

from pathlib import Path
from string import Template

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def render_template(name, **bindings):
    source = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    return Template(source).substitute(bindings)
