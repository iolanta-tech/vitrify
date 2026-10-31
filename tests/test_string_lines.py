"""Check string-line boundaries and Flake8 integration."""

import ast
import subprocess
import sys
import unittest
from pathlib import Path

from project_checks.string_lines import StringLinesChecker

ROOT = Path(__file__).resolve().parents[1]
THREE_LINES = 'MESSAGE = """one\ntwo\nthree"""\n'
FOUR_LINES = 'MESSAGE = """one\ntwo\nthree\nfour"""\n'
ERROR_CODE = "VIT001"


def violations(source):
    return list(StringLinesChecker(ast.parse(source)).run())


def flake8(source, filename):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "flake8",
            "--config",
            str(ROOT / ".flake8"),
            "--select",
            ERROR_CODE,
            "--stdin-display-name",
            filename,
            "-",
        ],
        input=source,
        text=True,
        capture_output=True,
        cwd=ROOT,
    )


class StringBoundaryTests(unittest.TestCase):
    def test_three_lines_allowed(self):
        self.assertEqual(violations(THREE_LINES), [])

    def test_four_lines_rejected(self):
        found = violations(FOUR_LINES)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][:2], (1, 10))
        self.assertIn("4 source lines (maximum 3)", found[0][2])

    def test_delimiter_lines_count(self):
        self.assertEqual(len(violations('MESSAGE = """\none\ntwo\n"""\n')), 1)

    def test_escaped_newlines_keep_one_source_line(self):
        self.assertEqual(violations(r'MESSAGE = "one\ntwo\nthree\nfour"'), [])

    def test_implicit_concatenation_counts_full_span(self):
        self.assertEqual(
            len(violations('MESSAGE = ("one"\n "two"\n "three"\n "four")\n')), 1
        )

    def test_fstring_reports_once(self):
        source = FOUR_LINES.replace('"""one', 'f"""{name}', 1)
        self.assertEqual(len(violations(source)), 1)

    def test_bytes_are_checked(self):
        source = FOUR_LINES.replace('"""one', 'b"""one', 1)
        self.assertEqual(len(violations(source)), 1)


class StringExemptionTests(unittest.TestCase):
    def test_real_docstrings_are_exempt(self):
        docstring = '"""one\ntwo\nthree\nfour"""\n'
        for declaration in (
            "",
            "class Example:\n",
            "def example():\n",
            "async def example():\n",
        ):
            with self.subTest(declaration=declaration):
                body = (
                    "\n".join(f"    {line}" for line in docstring.splitlines())
                    if declaration
                    else docstring
                )
                self.assertEqual(violations(f"{declaration}{body}"), [])

    def test_later_standalone_strings_are_checked(self):
        literal = FOUR_LINES.removeprefix("MESSAGE = ")
        source = f"marker = 1\n{literal}"
        self.assertEqual(len(violations(source)), 1)

    def test_fstrings_and_bytes_are_not_docstrings(self):
        for prefix in ("f", "b"):
            literal = FOUR_LINES.removeprefix("MESSAGE = ")
            source = f"{prefix}{literal}"
            with self.subTest(prefix=prefix):
                self.assertEqual(len(violations(source)), 1)


class StringPluginTests(unittest.TestCase):
    def test_flake8_loads_local_checker(self):
        completed = flake8(FOUR_LINES, "example.py")
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn(ERROR_CODE, completed.stdout)
        self.assertEqual(flake8(THREE_LINES, "example.py").returncode, 0)

    def test_flake8_exempts_test_fixtures(self):
        completed = flake8(FOUR_LINES, "tests/fixture.py")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
