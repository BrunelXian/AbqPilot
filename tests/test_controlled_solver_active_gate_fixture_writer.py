import json
from pathlib import Path

from abqpilot.gui.controlled_solver_active_gate_fixture_writer import write_controlled_solver_active_gate_fixture
from abqpilot.gui.controlled_solver_active_gate_schema import build_controlled_solver_active_gate_schema


def test_fixture_writer_writes_active_gate_only_under_tmp_path(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.inp"
    candidate.write_text("*Heading\n", encoding="utf-8")
    result = write_controlled_solver_active_gate_fixture(
        tmp_path,
        fixture_mode=True,
        task_id="fixture_task",
        task_dir=tmp_path,
        candidate_artifact_path=candidate,
    )
    assert result["writer_status"] == "ACTIVE_GATE_WRITER_FIXTURE_WRITE_OK"
    gate_path = Path(result["output_paths"]["fixture_gate_record"])
    record = json.loads(gate_path.read_text(encoding="utf-8"))
    assert record["fixture_only"] is True
    assert record["real_project_gate_written"] is False
    assert record["solver_approved"] is True
    assert record["solver_execution_allowed"] is False
    assert record["solver_request_created"] is False
    assert record["solver_run"] is False
    assert record["queue_runner_launched"] is False
    assert record["odb_opened"] is False
    assert record["final_evidence_approved"] is False
    assert record["final_verdict_frozen"] is False
    assert record["task_final_evidence_ledger_updated"] is False
    assert not (tmp_path / "solver_request.json").exists()
    assert not (tmp_path / "handoffs").exists()
    assert not (tmp_path / "TASK_FINAL_EVIDENCE_LEDGER.md").exists()


def test_fixture_writer_blocks_unsafe_requests(tmp_path: Path) -> None:
    base = build_controlled_solver_active_gate_schema("fixture_task", tmp_path)
    cases = [
        ({"solver_request_created": True}, "ACTIVE_GATE_WRITER_BLOCKED_SOLVER_REQUEST"),
        ({"solver_execution_allowed": True}, "ACTIVE_GATE_WRITER_BLOCKED_EXECUTION_HANDOFF"),
        ({"final_evidence_approved": True}, "ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE"),
        ({"final_verdict_frozen": True}, "ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE"),
    ]
    for changes, status in cases:
        record = dict(base)
        record.update(changes)
        result = write_controlled_solver_active_gate_fixture(tmp_path, fixture_mode=True, gate_record=record)
        assert result["writer_status"] == status


def test_fixture_writer_blocks_real_task_and_requested_outputs(tmp_path: Path) -> None:
    real = write_controlled_solver_active_gate_fixture(
        r"D:\Projects\AbqPilot-v2\runs\tasks\example\gates",
        fixture_mode=True,
    )
    assert real["writer_status"] == "ACTIVE_GATE_WRITER_BLOCKED_REAL_TASK_GATE_PATH"
    assert write_controlled_solver_active_gate_fixture(tmp_path, fixture_mode=True, request_solver_request=True)["writer_status"] == "ACTIVE_GATE_WRITER_BLOCKED_SOLVER_REQUEST"
    assert write_controlled_solver_active_gate_fixture(tmp_path, fixture_mode=True, request_execution_handoff=True)["writer_status"] == "ACTIVE_GATE_WRITER_BLOCKED_EXECUTION_HANDOFF"
    assert write_controlled_solver_active_gate_fixture(tmp_path, fixture_mode=True, request_final_evidence=True)["writer_status"] == "ACTIVE_GATE_WRITER_BLOCKED_FINAL_EVIDENCE"
