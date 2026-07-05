from abqpilot.gui.high_risk_gate_catalog import get_high_risk_gate_catalog
from abqpilot.gui.high_risk_gate_preview import build_high_risk_gate_ux_spec
from abqpilot.gui.high_risk_gate_report import (
    render_high_risk_action_catalog_markdown,
    render_high_risk_gate_checklists_markdown,
    render_high_risk_gate_ux_report,
)


def test_high_risk_gate_reports_include_required_boundary_copy(tmp_path) -> None:
    spec = build_high_risk_gate_ux_spec(tmp_path)
    report = render_high_risk_gate_ux_report(spec)
    assert "High-risk action locked" in report
    assert "Preview only; not an approval" in report
    assert "No TASK_FINAL_EVIDENCE_LEDGER.md mutation" in report


def test_action_catalog_and_checklist_markdown_render() -> None:
    catalog = render_high_risk_action_catalog_markdown(get_high_risk_gate_catalog())
    checklists = render_high_risk_gate_checklists_markdown(build_high_risk_gate_ux_spec(".")["gate_previews"])
    assert "CONTROLLED_SOLVER_RUN" in catalog
    assert "StaticValidator" in checklists
    assert "NOT_EXECUTABLE" in checklists
