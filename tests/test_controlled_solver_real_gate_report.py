from abqpilot.gui.controlled_solver_real_gate_creation import create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_real_gate_report import render_no_execution_audit, render_real_gate_creation_report


def test_real_gate_report_confirms_no_execution(tmp_path) -> None:
    result = create_controlled_solver_real_gate_smoke(tmp_path)
    report = render_real_gate_creation_report(result["validation"] | {"task_id": result["task_id"], "gate_id": "GATE_001", "decision": "APPROVED_BY_HUMAN", "solver_approved": True}, result["validation"])
    audit = render_no_execution_audit(result)
    assert "Human approval gate creation does not execute solver" in report
    assert "No solver request files are created" in report
    assert "solver_execution_allowed: False" in audit
    assert "no_execution_handoff_found: True" in audit
