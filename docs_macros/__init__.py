"""Register the saved-example renderers with MkDocs."""

from docs_macros.sparqld_patterns import install as install_sparqld_patterns
from docs_macros.macros import define_env

__all__ = ["define_env", "install_sparqld_patterns"]
