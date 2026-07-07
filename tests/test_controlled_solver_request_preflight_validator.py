from abqpilot.gui.controlled_solver_request_preflight import build_controlled_solver_request_preflight_result
from abqpilot.gui.controlled_solver_request_policy import (
    validate_output_dir_policy,
    validate_resource_policy_shape,
    validate_solver_command_label_policy,
)
from abqpilot.gui.controlled_solver_request_preflight_validator import validate_controlled_solver_request_preflight_result


def _preflight() -> dict:
    command = validate_solver_command_label_policy("ABQ2024_FUTURE_CONTROLLED_SOLVER_STAGE", False, True)
    output = validate_output_dir_policy("runs/tasks/stage5_2f_controlled_solver_real_gate_smoke/future_controlled_solver_outputs", "runs/tasks/stage5_2f_controlled_solver_real_gate_smoke", False)
    output["output_dir_policy_validated"] = True
    resource = validate_resource_policy_shape({})
    return build_controlled_solver_request_preflight_result(
        "runs/tasks/stage5_2f_controlled_solver_real_gate_smoke",
        {"gate_id": "GATE_001"},
        {"draft_type": "CONTROLLED_SOLVER_EXECUTION_HANDOFF_DRAFT"},
        {"draft_type": "CONTROLLED_SOLVER_REQUEST_DRAFT"},
        "candidate.inp",
        "abc",
        command,
        output,
        resource,
    )


def test_request_preflight_validator_accepts_safe_result() -> None:
    assert validate_controlled_solver_request_preflight_result(_preflight())["validation_status"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_PASS_NO_EXECUTION"


def test_request_preflight_validator_blocks_unsafe_fields() -> None:
    cases = {
        "request_active": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_ACTIVE_REQUEST",
        "executable_request": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_ACTIVE_REQUEST",
        "solver_execution_allowed": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_EXECUTION_ALLOWED",
        "solver_request_created": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_SOLVER_REQUEST_CREATED",
        "solver_run": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_EXECUTION_ALLOWED",
        "queue_runner_launched": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_QUEUE_OR_ODB",
        "odb_opened": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_QUEUE_OR_ODB",
        "odb_metrics_approved": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_QUEUE_OR_ODB",
        "final_evidence_approved": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_FINAL_EVIDENCE",
        "final_verdict_frozen": "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_FINAL_EVIDENCE",
    }
    for field, status in cases.items():
        result = _preflight()
        result[field] = True
        assert validate_controlled_solver_request_preflight_result(result)["validation_status"] == status
    command_bad = _preflight()
    command_bad["solver_command_label_validated"] = False
    assert validate_controlled_solver_request_preflight_result(command_bad)["validation_status"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_SOLVER_COMMAND_POLICY"
    output_bad = _preflight()
    output_bad["output_dir_created"] = True
    assert validate_controlled_solver_request_preflight_result(output_bad)["validation_status"] == "CONTROLLED_SOLVER_REQUEST_PREFLIGHT_BLOCKED_OUTPUT_DIR_POLICY"
