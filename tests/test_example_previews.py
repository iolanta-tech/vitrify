"""Bound rendered results while retaining access to complete artifacts."""


from docs_macros.rendering.files import _result_code
from docs_macros.rendering.tables import csv_table


SOURCE_LINES = 50


class PreviewTests:
    def test_csv_rows_are_bounded(self):
        rows = "\n".join(str(number) for number in range(10))
        source = f"label\n{rows}"
        preview = csv_table(source, 5)
        assert "Showing 5 of 10 rows" in preview
        assert (preview.count("<td>")) == 5
        assert ("<td>9</td>") not in preview

    def test_plain_result_lines_are_bounded(self):
        source = "\n".join(str(number) for number in range(SOURCE_LINES))
        preview = _result_code(source, "text")
        assert "Showing 40 of 50 lines" in preview
        assert "    49\n" not in preview
