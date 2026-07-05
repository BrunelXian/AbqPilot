from pathlib import Path

from abqpilot.gui.markdown_preview import build_markdown_preview


def test_markdown_preview_parses_frontmatter_headings_and_boundaries(tmp_path: Path) -> None:
    path = tmp_path / "RUN_001.md"
    path.write_text(
        """---
doc_type: run_report
status: NON_SOLVER_EVIDENCE_SUMMARY_READY
final_evidence_approved: false
---
# RUN

## Claim Boundary
This is non-final.

## Guardrails / Forbidden Actions Confirmation
Solver and ODB remain disabled.
""",
        encoding="utf-8",
    )
    preview = build_markdown_preview(path)
    assert preview["parse_status"] == "ARTIFACT_PREVIEW_READY"
    assert preview["artifact_type"] == "RUN_REPORT"
    assert preview["frontmatter"]["doc_type"] == "run_report"
    assert any(item["title"] == "Claim Boundary" for item in preview["headings"])
    assert "non-final" in preview["claim_boundary_text"]
    assert "Solver" in preview["safety_boundary_text"]


def test_markdown_preview_flags_final_evidence_claim(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.md"
    path.write_text(
        """---
doc_type: gate_decision
final_evidence_approved: true
---
# Unsafe
""",
        encoding="utf-8",
    )
    preview = build_markdown_preview(path)
    assert preview["parse_status"] == "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
    assert preview["unsafe_claims"][0]["key"] == "final_evidence_approved"
