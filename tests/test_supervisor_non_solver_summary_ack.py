from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.non_solver_evidence_summary import generate_non_solver_evidence_summary
from abqpilot.acom.supervisor_non_solver_summary_ack import supervisor_ack_non_solver_summary
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_ready_non_solver_summary_becomes_acknowledged(tmp_path):
    task = _task_with_summary(tmp_path)
    final_ledger = task / "TASK_FINAL_EVIDENCE_LEDGER.md"
    before = final_ledger.read_text(encoding="utf-8")
    result = supervisor_ack_non_solver_summary(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED"
    details = result["details"]
    assert details["gate_decision"] == "ACKNOWLEDGED_NON_SOLVER_SUMMARY"
    assert details["final_evidence_approved"] is False
    assert details["final_verdict_frozen"] is False
    assert details["solver_approved"] is False
    assert details["odb_metrics_approved"] is False
    assert details["task_final_evidence_ledger_updated"] is False
    assert Path(details["ack_ledger_md_path"]).exists()
    run = load_frontmatter(details["run_record_path"])
    gate = load_frontmatter(details["gate_path"])
    handoff = load_frontmatter(details["handoff_path"])
    assert run["agent"] == "PipelineSupervisor"
    assert gate["decision"] == "ACKNOWLEDGED_NON_SOLVER_SUMMARY"
    assert gate["decision"] != "APPROVED"
    assert handoff["to_agent"] == "DocsStatusAgent"
    assert validate_task_protocol(task)["verdict"] == "PIPELINE_PROTOCOL_VALID"
    assert final_ledger.read_text(encoding="utf-8") == before


def test_ready_with_warnings_summary_becomes_acknowledged_with_warnings(tmp_path):
    task = _task_with_summary(tmp_path, warning=True)
    result = supervisor_ack_non_solver_summary(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED_WITH_WARNINGS"
    assert result["details"]["gate_decision"] == "ACKNOWLEDGED_NON_SOLVER_SUMMARY_WITH_WARNINGS"


def test_missing_summary_blocks_acknowledgement(tmp_path):
    task = _task(tmp_path)
    _write_ledger(task)
    result = supervisor_ack_non_solver_summary(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_SUMMARY"
    assert result["output_paths"]["handoff"] is None


def test_invalid_and_blocked_summary_block_acknowledgement(tmp_path):
    task = _task_with_summary(tmp_path / "invalid")
    summary_path = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["summary_status"] = "NOPE"
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    assert supervisor_ack_non_solver_summary(task)["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SUMMARY_NOT_READY"

    task2 = _task_with_summary(tmp_path / "blocked")
    summary_path2 = task2 / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"
    payload2 = json.loads(summary_path2.read_text(encoding="utf-8"))
    payload2["summary_status"] = "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_MISSING_LEDGER"
    payload2["gate_decision"] = "BLOCKED"
    payload2["handoff_path"] = None
    summary_path2.write_text(json.dumps(payload2), encoding="utf-8")
    assert supervisor_ack_non_solver_summary(task2)["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SUMMARY_NOT_READY"


def test_missing_and_invalid_ledger_blocks_acknowledgement(tmp_path):
    task = _task_with_summary(tmp_path / "missing_ledger")
    (task / "NON_SOLVER_EVIDENCE_LEDGER.json").unlink()
    assert supervisor_ack_non_solver_summary(task)["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_MISSING_LEDGER"

    task2 = _task_with_summary(tmp_path / "invalid_ledger")
    (task2 / "NON_SOLVER_EVIDENCE_LEDGER.json").write_text(json.dumps({"schema_version": "0.1", "ledger_type": "wrong", "entries": []}), encoding="utf-8")
    assert supervisor_ack_non_solver_summary(task2)["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_LEDGER_INVALID"


def test_unsafe_summary_flags_block_acknowledgement(tmp_path):
    for field, expected in [
        ("final_evidence_approved", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("final_verdict_frozen", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("solver_approved", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"),
        ("odb_metrics_approved", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"),
        ("task_final_evidence_ledger_updated", "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_BLOCKED_TASK_FINAL_LEDGER_MUTATION"),
    ]:
        task = _task_with_summary(tmp_path / field)
        summary_path = task / "evidence_report" / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json"
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
        payload[field] = True
        summary_path.write_text(json.dumps(payload), encoding="utf-8")
        assert supervisor_ack_non_solver_summary(task)["verdict"] == expected


def _task_with_summary(tmp_path: Path, warning: bool = False) -> Path:
    task = _task(tmp_path)
    _write_ledger(task, warning=warning)
    generate_non_solver_evidence_summary(task)
    return task


def _task(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    return root / "runs" / "tasks" / "task"


def _write_ledger(task: Path, warning: bool = False) -> None:
    task.joinpath("NON_SOLVER_EVIDENCE_LEDGER.md").write_text("# Non-Solver Evidence Ledger\n\nNon-final.\n", encoding="utf-8")
    task.joinpath("NON_SOLVER_EVIDENCE_LEDGER.json").write_text(
        json.dumps({"schema_version": "0.1", "ledger_type": "non_solver_evidence", "entries": [_entry(warning)]}),
        encoding="utf-8",
    )


def _entry(warning: bool = False) -> dict:
    return {
        "task_id": "task",
        "source_revalidation_agent": "DocsStatusAgent",
        "source_revalidation_status": "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR" if warning else "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
        "supervisor_review_status": "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_WITH_WARNINGS_FOR_LEDGER" if warning else "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER",
        "ledger_decision": "ACCEPTED_WITH_WARNINGS_FOR_NON_SOLVER_EVIDENCE_LEDGER" if warning else "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER",
        "artifacts_reviewed": [],
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
    }
