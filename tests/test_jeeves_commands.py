"""Keep internal helpers out of the public Jeeves command list."""

import unittest
from pathlib import Path

from jeeves_shell.discover import retrieve_commands_from_jeeves_file


class JeevesCommandTests(unittest.TestCase):
    def test_public_commands(self):
        root = Path(__file__).resolve().parents[1]
        names = {name for name, _ in retrieve_commands_from_jeeves_file(root)}
        self.assertEqual(names, {"examples", "serve", "fmt", "lint"})
