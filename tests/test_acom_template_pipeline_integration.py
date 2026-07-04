from __future__ import annotations

from pathlib import Path

from abqpilot.acom.template_renderer import render_pipeline_acom_handoff


def test_high_risk_template_creates_pending_revalidation_gate(tmp_path) -> None:
    result = render_pipeline_acom_handoff(task_id="gate_smoke", template_id="controlled_execution_planning", project_root=tmp_path)
    gate_path = Path(result["gate_path"])
    assert gate_path.exists()
    text = gate_path.read_text(encoding="utf-8")
    assert "decision: PENDING_REVALIDATION" in text
    assert "ACOM output is not final evidence" in text
