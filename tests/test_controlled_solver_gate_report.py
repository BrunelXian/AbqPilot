from abqpilot.gui.controlled_solver_gate_preview import build_controlled_solver_gate_preview
from abqpilot.gui.controlled_solver_gate_report import (
    render_controlled_solver_approval_token_rules,
    render_controlled_solver_gate_preview_report,
)


def test_controlled_solver_gate_report_includes_separation_copy(tmp_path) -> None:
    preview = build_controlled_solver_gate_preview(tmp_path)
    report = render_controlled_solver_gate_preview_report(preview)
    assert "Preview only; not a solver approval" in report
    assert "No solver request file is created" in report
    assert "Future solver approval and future solver execution must be separate stages" in report


def test_token_rules_report_mentions_active_approval_block() -> None:
    report = render_controlled_solver_approval_token_rules(["active_approval must be false in Stage 5.2B"])
    assert "TOKEN_PREVIEW_BLOCKED_ACTIVE_APPROVAL_ATTEMPT" in report
    assert "preview-only in Stage 5.2B" in report
