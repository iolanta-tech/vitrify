"""Check string-line boundaries and Flake8 integration."""

import ast
import sys
from pathlib import Path

import sh

from project_checks.string_lines import StringLinesChecker

ROOT = Path(__file__).resolve().parents[1]
THREE_LINES = 'MESSAGE = """one\ntwo\nthree"""\n'
FOUR_LINES = 'MESSAGE = """one\ntwo\nthree\nfour"""\n'
ERROR_CODE = "VIT001"
EXIT_STATUS_LIMIT = 256
ANY_EXIT = range(EXIT_STATUS_LIMIT)


def violations(source):
    return list(StringLinesChecker(ast.parse(source)).run())


def flake8(source, filename):
    return sh.Command(sys.executable)(
        "-m",
        "flake8",
        "--config",
        str(ROOT / ".flake8"),
        "--select",
        ERROR_CODE,
        "--stdin-display-name",
        filename,
        "-",
        _in=source,
        _cwd=str(ROOT),
        _ok_code=ANY_EXIT,
        _return_cmd=True,
    )


class StringBoundaryTests:
    def test_three_lines_allowed(self):
        assert violations(THREE_LINES) == []

    def test_four_lines_rejected(self):
        found = violations(FOUR_LINES)
        assert len(found) == 1
        assert found[0][:2] == (1, 10)
        assert "4 source lines (maximum 3)" in found[0][2]

    def test_delimiter_lines_count(self):
        assert len(violations('MESSAGE = """\none\ntwo\n"""\n')) == 1

    def test_escaped_newlines_keep_one_source_line(self):
        assert violations(r'MESSAGE = "one\ntwo\nthree\nfour"') == []

    def test_implicit_concatenation_counts_full_span(self):
        assert len(violations('MESSAGE = ("one"\n "two"\n "three"\n "four")\n')) == 1

    def test_fstring_reports_once(self):
        source = FOUR_LINES.replace('"""one', 'f"""{name}', 1)
        assert len(violations(source)) == 1

    def test_bytes_are_checked(self):
        source = FOUR_LINES.replace('"""one', 'b"""one', 1)
        assert len(violations(source)) == 1


class StringExemptionTests:
    def test_real_docstrings_are_exempt(self):
        docstring = '"""one\ntwo\nthree\nfour"""\n'
        for declaration in (
            "",
            "class Example:\n",
            "def example():\n",
            "async def example():\n",
        ):
            body = (
                "\n".join(f"    {line}" for line in docstring.splitlines())
                if declaration
                else docstring
            )
            assert violations(f"{declaration}{body}") == []

    def test_later_standalone_strings_are_checked(self):
        literal = FOUR_LINES.removeprefix("MESSAGE = ")
        source = f"marker = 1\n{literal}"
        assert len(violations(source)) == 1

    def test_fstrings_and_bytes_are_not_docstrings(self):
        for prefix in ("f", "b"):
            literal = FOUR_LINES.removeprefix("MESSAGE = ")
            source = f"{prefix}{literal}"
            assert len(violations(source)) == 1


class StringPluginTests:
    def test_flake8_loads_local_checker(self):
        completed = flake8(FOUR_LINES, "example.py")
        assert completed.exit_code == 1, completed.stderr.decode()
        assert ERROR_CODE in completed.stdout.decode()
        assert flake8(THREE_LINES, "example.py").exit_code == 0

    def test_flake8_exempts_test_fixtures(self):
        completed = flake8(FOUR_LINES, "tests/fixture.py")
        output = completed.stdout.decode() + completed.stderr.decode()
        assert completed.exit_code == 0, output
