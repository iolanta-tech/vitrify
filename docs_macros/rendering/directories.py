"""Render generated crate files as a linked directory tree."""

from docs_macros.history import captures, selected_capture
from docs_macros.rendering import artifacts
from docs_macros.storage import page_name


def directory_preview(example, attempt=None, endpoint=None):
    if not captures(example, endpoint):
        return ""
    crate_dir = selected_capture(example, attempt, endpoint).directory
    example = page_name(example)
    lines = [f":material-folder-open: `{example}/`  "]
    lines.extend(_tree_lines(crate_dir))
    return "\n".join(lines)


def _tree_line(crate_dir, file_path, last):
    media_type = artifacts.file_media_type(crate_dir, file_path.name)
    icon = artifacts.file_icon(file_path.name, media_type)
    branch = "└──" if last else "├──"
    anchor = artifacts.anchor_id(file_path.name)
    return f"{branch} :{icon}: [`{file_path.name}`](#{anchor})  "


def _tree_lines(crate_dir):
    files = artifacts.crate_files(crate_dir)
    return (
        _tree_line(crate_dir, file_path, index == len(files) - 1)
        for index, file_path in enumerate(files)
    )
