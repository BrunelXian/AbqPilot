from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.non_solver_evidence_summary import generate_non_solver_evidence_summary
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_valid_non_solver_ledger_creates_summary_and_pipeline_records(tmp_path):
    task = _task(tmp_path)
    final_ledger = task / "TASK_FINAL_EVIDENCE_LEDGER.md"
    before = final_ledger.read_text(encoding="utf-8")
    _write_ledger(task)
    result = generate_non_solver_evidence_summary(task)
    assert result["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_READY"
    details = result["details"]
    assert details["final_evidence_approved"] is False
    assert details["final_verdict_frozen"] is False
    assert details["solver_approved"] is False
    assert details["odb_metrics_approved"] is False
    assert details["task_final_evidence_ledger_updated"] is False
    assert Path(details["summary_result_path"]).exists()
    assert Path(details["summary_report_path"]).read_text(encoding="utf-8").count("non-final") >= 1
    run = load_frontmatter(details["run_record_path"])
    gate = load_frontmatter(details["gate_path"])
    handoff = load_frontmatter(details["handoff_path"])
    assert run["agent"] == "EvidenceReportAgent"
    assert gate["decision"] == "NON_SOLVER_SUMMARY_READY_PENDING_SUPERVISOR_ACK"
    assert gate["decision"] != "APPROVED"
    assert handoff["to_agent"] == "PipelineSupervisor"
    assert validate_task_protocol(task)["verdict"] == "PIPELINE_PROTOCOL_VALID"
    assert final_ledger.read_text(encoding="utf-8") == before


def test_warning_ledger_creates_warning_summary(tmp_path):
    task = _task(tmp_path)
    _write_ledger(task, warning=True)
    result = generate_non_solver_evidence_summary(task)
    assert result["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_READY_WITH_WARNINGS"
    assert result["details"]["gate_decision"] == "NON_SOLVER_SUMMARY_READY_WITH_WARNINGS_PENDING_SUPERVISOR_ACK"


def test_missing_ledger_blocks_without_advancing_handoff(tmp_path):
    task = _task(tmp_path)
    result = generate_non_solver_evidence_summary(task)
    assert result["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_MISSING_LEDGER"
    assert result["details"]["gate_decision"] == "BLOCKED"
    assert result["output_paths"]["handoff"] is None


def test_empty_and_invalid_ledgers_block(tmp_path):
    task = _task(tmp_path / "empty")
    (task / "NON_SOLVER_EVIDENCE_LEDGER.md").write_text("# Non-Solver Evidence Ledger\n", encoding="utf-8")
    (task / "NON_SOLVER_EVIDENCE_LEDGER.json").write_text(json.dumps({"schema_version": "0.1", "ledger_type": "non_solver_evidence", "entries": []}), encoding="utf-8")
    assert generate_non_solver_evidence_summary(task)["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_EMPTY_LEDGER"

    task2 = _task(tmp_path / "invalid")
    (task2 / "NON_SOLVER_EVIDENCE_LEDGER.md").write_text("# Non-Solver Evidence Ledger\n", encoding="utf-8")
    (task2 / "NON_SOLVER_EVIDENCE_LEDGER.json").write_text(json.dumps({"schema_version": "0.1", "ledger_type": "wrong", "entries": [_entry()]}), encoding="utf-8")
    assert generate_non_solver_evidence_summary(task2)["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_LEDGER_INVALID"


def test_unsafe_ledger_entries_block(tmp_path):
    for field, expected in [
        ("final_evidence_approved", "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("final_verdict_frozen", "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("solver_approved", "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"),
        ("odb_metrics_approved", "NON_SOLVER_EVIDENCE_SUMMARY_BLOCKED_SOLVER_OR_ODB_APPROVAL_ATTEMPT"),
    ]:
        task = _task(tmp_path / field)
        entry = _entry()
        entry[field] = True
        _write_ledger(task, entries=[entry])
        assert generate_non_solver_evidence_summary(task)["verdict"] == expected


def _task(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    task = root / "runs" / "tasks" / "task"
    handoff = task / "handoffs" / "HANDOFF_018_SUPERVISOR_NON_SOLVER_REVIEW_TO_EVIDENCE_REPORT_AGENT.md"
    handoff.write_text(
        "---\ndoc_type: handoff\ntask_id: task\nhandoff_id: HANDOFF_018\nfrom_agent: PipelineSupervisor\nto_agent: EvidenceReportAgent\nfrom_run: RUN_018\ntarget_run: NON_SOLVER_EVIDENCE_SUMMARY_PENDING\nrisk_level: LOW\nexpected_output: trace/RUN_XXX_EVIDENCE_REPORT_AGENT_NON_SOLVER_SUMMARY.md\n---\n",
        encoding="utf-8",
    )
    return task


def _write_ledger(task: Path, entries: list[dict] | None = None, warning: bool = False) -> None:
    task.joinpath("NON_SOLVER_EVIDENCE_LEDGER.md").write_text(
        "# Non-Solver Evidence Ledger\n\nThis ledger is non-final and non-solver only.\n",
        encoding="utf-8",
    )
    payload = {"schema_version": "0.1", "ledger_type": "non_solver_evidence", "entries": entries or [_entry(warning=warning)]}
    task.joinpath("NON_SOLVER_EVIDENCE_LEDGER.json").write_text(json.dumps(payload), encoding="utf-8")


def _entry(warning: bool = False) -> dict:
    return {
        "task_id": "task",
        "source_revalidation_agent": "DocsStatusAgent",
        "source_revalidation_status": "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR" if warning else "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
        "supervisor_review_status": "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_WITH_WARNINGS_FOR_LEDGER" if warning else "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER",
        "ledger_decision": "ACCEPTED_WITH_WARNINGS_FOR_NON_SOLVER_EVIDENCE_LEDGER" if warning else "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER",
        "artifacts_reviewed": [],
        "claim_boundary": "non-final",
        "limitations": ["warning"] if warning else [],
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
    }
