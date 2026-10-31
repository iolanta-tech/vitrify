"""Load project SPARQL files and refresh cached text when a file changes."""

from functools import lru_cache
from pathlib import Path

QUERIES_DIR = Path(__file__).resolve().parents[1] / "queries"
CACHE_SIZE = 32


def load_query(name):
    source = QUERIES_DIR / name
    return _read_query(source, source.stat().st_mtime_ns)


@lru_cache(maxsize=CACHE_SIZE)
def _read_query(source, _modified):
    return source.read_text(encoding="utf-8")
