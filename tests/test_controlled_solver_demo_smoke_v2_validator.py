from pathlib import Path

from abqpilot.gui.controlled_solver_demo_smoke_v2 import build_demo_gate_v2, build_demo_solver_request_v2, sha256_file
from abqpilot.gui.controlled_solver_demo_smoke_v2_validator import validate_demo_gate_v2, validate_demo_solver_request_v2


def test_demo_smoke_v2_gate_and_request_validate(tmp_path: Path) -> None:
    task = tmp_path / "runs" / "tasks" / "stage5_3a_v2_controlled_solver_demo_smoke"
    source = tmp_path / "runs" / "candidate.inp"
    copied = task / "artifacts" / "solver_inputs" / "demo_solver_smoke.inp"
    source.parent.mkdir(parents=True, exist_ok=True)
    copied.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("*Heading\n", encoding="utf-8")
    copied.write_text("*Heading\n", encoding="utf-8")
    gate = build_demo_gate_v2(task, source, copied, sha256_file(source), sha256_file(copied))
    request = build_demo_solver_request_v2(task, copied, sha256_file(copied))
    assert validate_demo_gate_v2(gate)["validation_status"] == "STAGE5_3A_V2_DEMO_GATE_VALID"
    assert validate_demo_solver_request_v2(request)["validation_status"] == "STAGE5_3A_V2_DEMO_SOLVER_REQUEST_VALID"


def test_demo_smoke_v2_validator_blocks_unsafe_flags(tmp_path: Path) -> None:
    task = tmp_path / "runs" / "tasks" / "stage5_3a_v2_controlled_solver_demo_smoke"
    copied = task / "artifacts" / "solver_inputs" / "demo_solver_smoke.inp"
    copied.parent.mkdir(parents=True, exist_ok=True)
    copied.write_text("*Heading\n", encoding="utf-8")
    request = build_demo_solver_request_v2(task, copied, sha256_file(copied))
    request["final_evidence_approved"] = True
    assert validate_demo_solver_request_v2(request)["validation_status"] == "STAGE5_3A_V2_DEMO_SOLVER_REQUEST_INVALID"
    request["final_evidence_approved"] = False
    request["task_id"] = "other_task"
    assert validate_demo_solver_request_v2(request)["validation_status"] == "STAGE5_3A_V2_DEMO_SOLVER_REQUEST_INVALID"
