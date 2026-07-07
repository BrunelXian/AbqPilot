import json
from pathlib import Path

from abqpilot.gui.controlled_solver_demo_smoke_v2 import TASK_ID, run_controlled_solver_demo_smoke_v2, select_solver_ready_demo_inp_v2, sha256_file


def _write_candidate(root: Path) -> Path:
    candidate = root / "runs" / "stage4_4_dflux_deactivated_controlled_solver_validation" / "run_20260703_232004_870667" / "candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver.inp"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("*Heading\n** Stage 5.3A-v2 test candidate\n", encoding="utf-8")
    return candidate


def test_demo_smoke_v2_creates_scoped_request_without_test_solver_invocation(tmp_path: Path) -> None:
    source = _write_candidate(tmp_path)
    before = sha256_file(source)
    result = run_controlled_solver_demo_smoke_v2(tmp_path, attempt_solver=False)
    assert result["task_id"] == TASK_ID
    assert result["command_verdict"] == "STAGE5_3A_V2_SOLVER_RUN_NOT_ATTEMPTED_BY_TEST_MODE"
    assert result["workspace_guard_passed"] is True
    assert result["forbidden_root_pre_scan_hits"] == 0
    assert result["forbidden_root_post_scan_hits"] == 0
    assert result["solver_request_created"] is True
    assert result["smoke_demo_only"] is True
    assert result["arbitrary_task_execution_allowed"] is False
    assert result["queue_runner_launched"] is False
    assert result["odb_opened"] is False
    assert result["metrics_extracted"] is False
    assert result["final_evidence_approved"] is False
    assert result["final_verdict_frozen"] is False
    assert result["task_final_evidence_ledger_updated"] is False
    assert sha256_file(source) == before
    task = tmp_path / "runs" / "tasks" / TASK_ID
    request = task / "artifacts" / "solver_requests" / "solver_request.json"
    status = task / "artifacts" / "solver_status" / "CONTROLLED_SOLVER_DEMO_RUN_STATUS.json"
    copied = task / "artifacts" / "solver_inputs" / "demo_solver_smoke.inp"
    gate = task / "gates" / "GATE_001_DEMO_SOLVER_EXECUTION_APPROVAL.json"
    assert request.exists()
    assert status.exists()
    assert copied.exists()
    assert gate.exists()
    request_data = json.loads(request.read_text(encoding="utf-8"))
    assert request_data["request_type"] == "CONTROLLED_SOLVER_DEMO_SMOKE_RUN"
    assert request_data["active_request"] is True
    assert request_data["executable_request"] is True
    assert request_data["smoke_demo_only"] is True
    assert request_data["arbitrary_task_execution_allowed"] is False
    assert request_data["queue_runner_allowed"] is False
    assert request_data["odb_open_allowed"] is False
    assert request_data["metrics_extraction_allowed"] is False
    assert request_data["final_evidence_approval_allowed"] is False
    assert not (task / "job_request.json").exists()
    assert not (task / "abaqus_job.json").exists()
    assert not (tmp_path / "TASK_FINAL_EVIDENCE_LEDGER.md").exists()


def test_demo_smoke_v2_does_not_select_dummy_or_source_sanity_base(tmp_path: Path) -> None:
    dummy = tmp_path / "runs" / "tasks" / "stage5_2f_controlled_solver_real_gate_smoke" / "artifacts" / "candidates" / "candidate_controlled_solver_smoke.inp"
    sanity = tmp_path / "cae_model" / "sanity_base" / "source.inp"
    dummy.parent.mkdir(parents=True, exist_ok=True)
    sanity.parent.mkdir(parents=True, exist_ok=True)
    dummy.write_text("*Heading\n", encoding="utf-8")
    sanity.write_text("*Heading\n", encoding="utf-8")
    allowed = _write_candidate(tmp_path)
    assert select_solver_ready_demo_inp_v2(tmp_path) == allowed
