from pathlib import Path

from abqpilot.gui.controlled_solver_request_policy import (
    validate_output_dir_policy,
    validate_resource_policy_shape,
    validate_solver_command_label_policy,
)


def test_solver_command_label_policy_validates_without_invocation() -> None:
    result = validate_solver_command_label_policy("ABQ2024_FUTURE_CONTROLLED_SOLVER_STAGE", False, True)
    assert result["policy_status"] == "SOLVER_COMMAND_LABEL_POLICY_VALID"
    assert result["solver_command_label_validated"] is True
    assert result["solver_command_path_not_invoked"] is True
    blocked = validate_solver_command_label_policy(r"D:\ABAQUS2024\Commands\abq2024.bat", False, True)
    assert blocked["policy_status"] == "SOLVER_COMMAND_LABEL_POLICY_BLOCKED"


def test_output_dir_policy_validates_without_creation(tmp_path: Path) -> None:
    task = tmp_path / "runs" / "tasks" / "stage5_2f_controlled_solver_real_gate_smoke"
    task.mkdir(parents=True)
    output = task / "future_controlled_solver_outputs"
    result = validate_output_dir_policy(str(output), task, False)
    assert result["policy_status"] == "OUTPUT_DIR_POLICY_VALID"
    assert result["output_dir_created"] is False
    assert not output.exists()
    blocked = validate_output_dir_policy(str(output), task, True)
    assert blocked["policy_status"] == "OUTPUT_DIR_POLICY_BLOCKED"


def test_resource_policy_shape_defaults() -> None:
    result = validate_resource_policy_shape({})
    assert result["policy_status"] == "RESOURCE_POLICY_SHAPE_VALID"
    assert result["cpu_policy_validated"] is True
    assert result["memory_policy_validated"] is True
    assert result["timeout_policy_validated"] is True
    assert result["log_capture_policy_validated"] is True
