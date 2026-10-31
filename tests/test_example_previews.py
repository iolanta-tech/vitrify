"""Bound rendered results while retaining access to complete artifacts."""

import unittest

from docs_macros.rendering.files import _result_code
from docs_macros.rendering.tables import csv_table


SOURCE_LINES = 50


class PreviewTests(unittest.TestCase):
    def test_csv_rows_are_bounded(self):
        rows = "\n".join(str(number) for number in range(10))
        source = f"label\n{rows}"
        preview = csv_table(source, 5)
        self.assertIn("Showing 5 of 10 rows", preview)
        self.assertEqual(preview.count("<td>"), 5)
        self.assertNotIn("<td>9</td>", preview)

    def test_plain_result_lines_are_bounded(self):
        source = "\n".join(str(number) for number in range(SOURCE_LINES))
        preview = _result_code(source, "text")
        self.assertIn("Showing 40 of 50 lines", preview)
        self.assertNotIn("    49\n", preview)
