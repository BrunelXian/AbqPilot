from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.non_solver_revalidation_executor import execute_non_solver_revalidation
from abqpilot.acom.result_schema import empty_structured_result
from abqpilot.acom.revalidation_scaffold import scaffold_acom_revalidation
from abqpilot.acom.supervisor_non_solver_review import supervisor_review_non_solver_revalidation
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_pass_pending_supervisor_becomes_accepted_for_ledger(tmp_path):
    task = _task_with_execution(tmp_path, "DocsStatusAgent", "docs_status_update")
    result = supervisor_review_non_solver_revalidation(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER"
    details = result["details"]
    assert details["gate_decision"] == "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER"
    assert details["final_evidence_approved"] is False
    assert details["final_verdict_frozen"] is False
    assert details["solver_approved"] is False
    assert details["odb_metrics_approved"] is False
    assert Path(details["ledger_md_path"]).exists()
    assert Path(details["ledger_json_path"]).exists()
    gate = load_frontmatter(details["gate_path"])
    assert gate["decision"] == "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER"
    assert gate["decision"] != "APPROVED"
    handoff = load_frontmatter(details["handoff_path"])
    assert handoff["to_agent"] == "EvidenceReportAgent"
    assert validate_task_protocol(task)["verdict"] == "PIPELINE_PROTOCOL_VALID"


def test_warning_pending_supervisor_becomes_accepted_with_warnings(tmp_path):
    task = _task_with_execution(tmp_path, "SoftwareQAAgent", "test_expansion", qa_sparse=True)
    result = supervisor_review_non_solver_revalidation(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_WITH_WARNINGS_FOR_LEDGER"
    assert result["details"]["gate_decision"] == "ACCEPTED_WITH_WARNINGS_FOR_NON_SOLVER_EVIDENCE_LEDGER"


def test_fail_blocked_becomes_supervisor_blocked(tmp_path):
    task = _task_with_execution(tmp_path, "DocsStatusAgent", "docs_status_update")
    result_path = _latest_result(task)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["result_status"] = "NON_SOLVER_REVALIDATION_FAIL_BLOCKED"
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    result = supervisor_review_non_solver_revalidation(task, revalidation_result=result_path)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FAILED_REVALIDATION"
    assert not (task / "NON_SOLVER_EVIDENCE_LEDGER.json").exists()


def test_high_risk_agent_is_blocked(tmp_path):
    task = _task_with_execution(tmp_path, "GuardAgent", "mcpguard_review")
    result = supervisor_review_non_solver_revalidation(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_HIGH_RISK_AGENT"
    assert result["details"]["gate_decision"] == "BLOCKED"


def test_unsupported_agent_is_blocked(tmp_path):
    task = _task_with_execution(tmp_path, "DocsStatusAgent", "docs_status_update")
    result_path = _latest_result(task)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["downstream_agent"] = "UnknownAgent"
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    result = supervisor_review_non_solver_revalidation(task, revalidation_result=result_path)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSUPPORTED_AGENT"


def test_missing_result_is_blocked(tmp_path):
    task = _base_task(tmp_path)
    result = supervisor_review_non_solver_revalidation(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_MISSING_RESULT"


def test_approval_attempts_are_blocked(tmp_path):
    for field, expected in [
        ("final_evidence_approved", "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("final_verdict_frozen", "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("solver_approved", "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
        ("odb_metrics_approved", "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_FINAL_EVIDENCE_APPROVAL_ATTEMPT"),
    ]:
        task = _task_with_execution(tmp_path / field, "DocsStatusAgent", "docs_status_update")
        result_path = _latest_result(task)
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload[field] = True
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        result = supervisor_review_non_solver_revalidation(task, revalidation_result=result_path)
        assert result["verdict"] == expected


def test_automatic_execution_and_unsafe_flags_are_blocked(tmp_path):
    task = _task_with_execution(tmp_path / "auto", "DocsStatusAgent", "docs_status_update")
    result_path = _latest_result(task)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["automatic_execution_performed"] = True
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    assert supervisor_review_non_solver_revalidation(task, revalidation_result=result_path)["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_AUTOMATIC_EXECUTION"

    task2 = _task_with_execution(tmp_path / "unsafe", "DocsStatusAgent", "docs_status_update")
    result_path2 = _latest_result(task2)
    payload2 = json.loads(result_path2.read_text(encoding="utf-8"))
    payload2["safety_flags"]["odb_opened"] = True
    result_path2.write_text(json.dumps(payload2), encoding="utf-8")
    assert supervisor_review_non_solver_revalidation(task2, revalidation_result=result_path2)["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_UNSAFE_FLAGS"


def test_missing_stage5f_records_are_blocked(tmp_path):
    task = _task_with_execution(tmp_path, "DocsStatusAgent", "docs_status_update")
    result_path = _latest_result(task)
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    Path(payload["gate_path"]).unlink()
    result = supervisor_review_non_solver_revalidation(task, revalidation_result=result_path)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_REVIEW_BLOCKED_MISSING_RECORDS"


def _base_task(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    return root / "runs" / "tasks" / "task"


def _task_with_execution(tmp_path: Path, agent: str, template: str, qa_sparse: bool = False) -> Path:
    task = _base_task(tmp_path)
    (task / "codex_result").mkdir(exist_ok=True)
    handoff = task / "handoffs" / f"HANDOFF_009_ACOM_RESULT_TO_{agent.upper()}.md"
    handoff.write_text(
        f"---\ndoc_type: handoff\ntask_id: task\nhandoff_id: HANDOFF_009\nfrom_agent: ACOMAgent\nto_agent: {agent}\nfrom_run: RUN_010\ntarget_run: RUN_REVALIDATION_PENDING\nrisk_level: LOW\nexpected_output: trace/RUN_XXX_REVALIDATION.md\n---\n",
        encoding="utf-8",
    )
    structured = empty_structured_result("task", "acom_test")
    if not qa_sparse:
        structured["tests_run"] = ["pytest -q: passed"]
        structured["artifacts"] = {"tests_result": "passed", "safety_audit": "passed", "secret_audit": "passed", "eligibility_gates": ["human approval"]}
    structured["known_limitations"] = ["unit test"]
    (task / "codex_result" / "structured_result.json").write_text(json.dumps(structured), encoding="utf-8")
    (task / "codex_result" / "acom_result_intake.json").write_text(json.dumps({
        "task_id": "task",
        "handoff_id": "acom_test",
        "template_id": template,
        "result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        "downstream_agent": agent,
        "result_json": str(task / "codex_result" / "structured_result.json"),
        "downstream_handoff_path": str(handoff),
    }), encoding="utf-8")
    scaffold_acom_revalidation(task, downstream_agent=agent, revalidation_id="test")
    execute_non_solver_revalidation(task)
    return task


def _latest_result(task: Path) -> Path:
    return sorted((task / "revalidation").glob("*_*/REVALIDATION_EXECUTION_RESULT.json"), key=lambda path: path.stat().st_mtime)[-1]
