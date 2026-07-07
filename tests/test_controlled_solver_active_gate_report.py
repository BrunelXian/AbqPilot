from abqpilot.gui.controlled_solver_active_gate_report import (
    render_active_gate_design_report,
    render_active_gate_validation_rules,
)
from abqpilot.gui.controlled_solver_active_gate_schema import build_controlled_solver_active_gate_schema, build_future_execution_handoff_shape
from abqpilot.gui.controlled_solver_active_gate_validator import validate_controlled_solver_active_gate_schema


def test_active_gate_report_copy() -> None:
    gate = build_controlled_solver_active_gate_schema()
    validation = validate_controlled_solver_active_gate_schema(gate)
    report = render_active_gate_design_report(gate, validation, build_future_execution_handoff_shape(gate))
    assert "Active gate record design only" in report
    assert "No real project gate is written in Stage 5.2D" in report
    assert "Human approval does not execute solver" in report
    assert "Final evidence remains locked" in report
    assert "ODB and metrics remain disabled" in report
    assert "Queue mutation remains disabled" in report
    assert "solver_execution_allowed must be false" in render_active_gate_validation_rules()
