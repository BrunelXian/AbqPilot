from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage5_2a_docs_define_preview_only_high_risk_gate_ux() -> None:
    doc = (ROOT / "docs" / "GUI_HIGH_RISK_GATE_UX.md").read_text(encoding="utf-8")
    assert "Stage 5.2A specifies high-risk gate UX only" in doc
    assert "does not enable high-risk execution" in doc
    assert "does not create real approving gates" in doc
    assert "No `TASK_FINAL_EVIDENCE_LEDGER.md` mutation" in doc


def test_agents_mentions_high_risk_gate_preview_boundaries() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "High-risk gate UX previews must not be confused with approval" in text
    assert 'No "Approve" or "Execute" callbacks may be added in Stage 5.2A' in text
    assert "final evidence locked state must remain visible" in text
