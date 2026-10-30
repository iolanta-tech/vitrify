"""Keep legacy capture locations independent of page names."""

from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "docs" / "examples"


def page_name(example):
    return "eu-capitals" if example == "basic-example" else example


def storage_name(example):
    return "basic-example" if page_name(example) == "eu-capitals" else example


def baseline_directory(directory):
    return directory / "eu-capitals" if directory.name == "basic-example" else directory
