"""Render documentation fragments stored beside the project sources."""

from pathlib import Path
from string import Template

from jinja2 import Environment, StrictUndefined

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def render_template(name, **bindings):
    source = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    return Template(source).substitute(bindings)


def render_jinja(template, **bindings):
    source = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
    environment = Environment(autoescape=False, undefined=StrictUndefined)
    return environment.from_string(source).render(**bindings)
