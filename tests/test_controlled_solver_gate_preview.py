from pathlib import Path

from abqpilot.gui.controlled_solver_gate_preview import build_controlled_solver_gate_preview, write_controlled_solver_gate_preview


def test_controlled_solver_gate_preview_required_flags(tmp_path: Path) -> None:
    preview = build_controlled_solver_gate_preview(tmp_path)
    assert preview["gate_type"] == "CONTROLLED_SOLVER_RUN"
    assert preview["preview_only"] is True
    assert preview["approval_status"] == "NOT_APPROVED"
    assert preview["execution_status"] == "NOT_EXECUTABLE"
    assert preview["real_gate_created"] is False
    assert preview["solver_approved"] is False
    assert preview["solver_run"] is False
    assert preview["solver_request_created"] is False
    assert preview["queue_runner_launched"] is False
    assert preview["odb_opened"] is False
    assert preview["final_evidence_approved"] is False
    assert preview["final_verdict_frozen"] is False
    assert preview["task_final_evidence_ledger_updated"] is False


def test_write_controlled_solver_gate_preview_outputs(tmp_path: Path) -> None:
    result = write_controlled_solver_gate_preview(tmp_path, task_dir=tmp_path)
    assert result["verdict"] == "CONTROLLED_SOLVER_GATE_PREVIEW_REPORT_READY"
    paths = result["output_paths"]
    for path in paths.values():
        assert Path(path).exists()
    preview = result["details"]
    assert preview["approval_token_preview"]["active_approval"] is False
    assert preview["real_gate_created"] is False
    assert preview["solver_request_created"] is False
    assert preview["task_final_evidence_ledger_updated"] is False
