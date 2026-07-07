from pathlib import Path

from abqpilot.gui.controlled_solver_execution_handoff_draft import create_controlled_solver_execution_handoff_draft_no_exec
from abqpilot.gui.controlled_solver_real_gate_creation import SMOKE_TASK_ID, create_controlled_solver_real_gate_smoke
from abqpilot.gui.controlled_solver_request_audit import audit_controlled_solver_request_draft_no_execution
from abqpilot.gui.controlled_solver_request_draft import create_controlled_solver_request_draft_no_exec


def test_request_no_execution_audit_passes(tmp_path: Path) -> None:
    create_controlled_solver_real_gate_smoke(tmp_path)
    create_controlled_solver_execution_handoff_draft_no_exec(tmp_path)
    result = create_controlled_solver_request_draft_no_exec(tmp_path)
    task = tmp_path / "runs" / "tasks" / SMOKE_TASK_ID
    audit = audit_controlled_solver_request_draft_no_execution(task, result["draft"])
    assert audit["audit_status"] == "CONTROLLED_SOLVER_REQUEST_DRAFT_NO_EXECUTION_AUDIT_PASS"
    assert audit["no_solver_request_files_found"] is True
    assert audit["no_active_handoff_files_found"] is True
    assert audit["no_queue_files_found"] is True
    assert audit["no_odb_files_found"] is True
    assert audit["no_metrics_files_found"] is True
    for name in ("solver_request.json", "job_request.json", "abaqus_job.json", "run_solver.bat", "run_solver.cmd", "TASK_FINAL_EVIDENCE_LEDGER.md"):
        assert not (task / name).exists()
    assert not any(task.rglob("*.odb"))
    assert not any(task.rglob("*metrics*"))
