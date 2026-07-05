from __future__ import annotations

from pathlib import Path

from abqpilot.gui.read_only_document_view import build_read_only_document_view


def test_read_only_document_view_module_imports(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("---\ndoc_type: run_report\nstatus: READY\n---\nBody\n", encoding="utf-8")
    view = build_read_only_document_view(path)
    assert view["read_only"] is True
    assert view["editable"] is False
    assert view["frontmatter"]["doc_type"] == "run_report"
    assert view["first_lines"] == ["Body"]


def test_read_only_document_view_missing_file_is_safe(tmp_path):
    view = build_read_only_document_view(tmp_path / "missing.md")
    assert view["exists"] is False
    assert view["read_only"] is True
