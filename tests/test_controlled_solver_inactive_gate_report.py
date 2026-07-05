from abqpilot.gui.controlled_solver_inactive_gate_draft import build_controlled_solver_inactive_gate_draft
from abqpilot.gui.controlled_solver_inactive_gate_report import render_controlled_solver_inactive_gate_report
from abqpilot.gui.controlled_solver_inactive_gate_validator import validate_controlled_solver_inactive_gate_draft


def test_inactive_gate_report_includes_required_boundary_copy(tmp_path) -> None:
    draft = build_controlled_solver_inactive_gate_draft(tmp_path)
    validation = validate_controlled_solver_inactive_gate_draft(draft)
    report = render_controlled_solver_inactive_gate_report(draft, validation)
    assert "Inactive draft only; not an approval" in report
    assert "No active gate record is created in Stage 5.2C" in report
    assert "Future active human approval gate creation must be a separate explicit stage" in report
    assert "Future solver execution must be a later separate explicit stage" in report
