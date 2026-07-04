from __future__ import annotations

from abqpilot.pipeline_protocol.frontmatter import parse_frontmatter_text, validate_frontmatter


def test_frontmatter_parser_detects_doc_type() -> None:
    frontmatter, body = parse_frontmatter_text("---\ndoc_type: run_report\ntask_id: demo\n---\n# Body\n")
    assert frontmatter["doc_type"] == "run_report"
    assert frontmatter["task_id"] == "demo"
    assert "# Body" in body


def test_frontmatter_validator_rejects_missing_required_keys(tmp_path) -> None:
    path = tmp_path / "RUN_001.md"
    path.write_text("---\ndoc_type: run_report\ntask_id: demo\n---\n# Body\n", encoding="utf-8")
    result = validate_frontmatter(path)
    assert result["valid"] is False
    assert any("run_id" in error for error in result["errors"])
