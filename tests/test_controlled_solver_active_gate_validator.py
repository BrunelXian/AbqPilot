from abqpilot.gui.controlled_solver_active_gate_schema import build_controlled_solver_active_gate_schema
from abqpilot.gui.controlled_solver_active_gate_validator import validate_controlled_solver_active_gate_schema


def test_validator_accepts_safe_schema_fixture(tmp_path) -> None:
    candidate = tmp_path / "candidate.inp"
    candidate.write_text("*Heading\n", encoding="utf-8")
    record = build_controlled_solver_active_gate_schema("task1", tmp_path, candidate)
    assert validate_controlled_solver_active_gate_schema(record)["validation_status"] == "ACTIVE_SOLVER_GATE_SCHEMA_VALID"


def test_validator_blocks_unsafe_flags() -> None:
    base = build_controlled_solver_active_gate_schema()
    cases = {
        "solver_execution_allowed": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_EXECUTION_ALLOWED",
        "solver_request_created": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_SOLVER_REQUEST_CREATED",
        "solver_run": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_SOLVER_ALREADY_RUN",
        "queue_runner_launched": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_QUEUE_MUTATION",
        "odb_opened": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_ODB_OPEN",
        "odb_metrics_approved": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_METRICS_APPROVAL",
        "final_evidence_approved": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_FINAL_EVIDENCE",
        "token_reuse_allowed": "ACTIVE_SOLVER_GATE_SCHEMA_BLOCKED_TOKEN_REUSE",
    }
    for field, status in cases.items():
        record = dict(base)
        record[field] = True
        assert validate_controlled_solver_active_gate_schema(record)["validation_status"] == status
