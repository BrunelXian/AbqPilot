from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.non_solver_revalidation_executor import execute_non_solver_revalidation
from abqpilot.acom.result_schema import empty_structured_result
from abqpilot.acom.revalidation_scaffold import scaffold_acom_revalidation
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_docs_status_agent_executes_non_solver_revalidation(tmp_path):
    task = _task_with_scaffold(tmp_path, "DocsStatusAgent", "docs_status_update")
    result = execute_non_solver_revalidation(task)
    assert result["verdict"] == "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR"
    details = result["details"]
    assert Path(details["result_path"]).exists()
    assert Path(details["report_path"]).exists()
    gate = load_frontmatter(details["gate_path"])
    assert gate["decision"] == "PENDING_SUPERVISOR_REVIEW"
    assert gate["decision"] != "APPROVED"
    assert gate["final_evidence_approved"] is False
    run = load_frontmatter(details["run_record_path"])
    assert run["automatic_execution_performed"] is False
    handoff = load_frontmatter(details["handoff_path"])
    assert handoff["to_agent"] == "PipelineSupervisor"
    assert validate_task_protocol(task)["verdict"] == "PIPELINE_PROTOCOL_VALID"


def test_supported_agents_execute(tmp_path):
    cases = [
        ("SoftwareQAAgent", "test_expansion"),
        ("AuditAgent", "read_only_audit"),
        ("EvidenceReportAgent", "documentation_update"),
        ("PipelineSupervisor", "controlled_execution_planning"),
    ]
    for agent, template in cases:
        task = _task_with_scaffold(tmp_path / agent, agent, template)
        result = execute_non_solver_revalidation(task)
        assert result["verdict"] in {
            "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
            "NON_SOLVER_REVALIDATION_WARNING_PENDING_SUPERVISOR",
        }
        assert result["details"]["final_evidence_approved"] is False


def test_high_risk_agents_block(tmp_path):
    for agent in ["GuardAgent", "CandidateBuilderAgent", "DiagnosisAgent", "ExecutionAgent", "MetricsAgent"]:
        task = _task_with_scaffold(tmp_path / agent, agent, "mcpguard_review")
        result = execute_non_solver_revalidation(task)
        assert result["verdict"] == "NON_SOLVER_REVALIDATION_BLOCKED_HIGH_RISK_AGENT"
        assert result["output_paths"]["gate"] is None


def test_rejected_acom_intake_blocks_execution(tmp_path):
    task = _task_with_scaffold(tmp_path, "DocsStatusAgent", "docs_status_update", status="ACOM_RESULT_REJECTED_SAFETY_FLAGS")
    result = execute_non_solver_revalidation(task)
    assert result["verdict"] == "NON_SOLVER_REVALIDATION_BLOCKED_ACOM_INTAKE_NOT_ACCEPTED"


def test_missing_scaffold_blocks(tmp_path):
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    task = root / "runs" / "tasks" / "task"
    result = execute_non_solver_revalidation(task)
    assert result["verdict"] == "NON_SOLVER_REVALIDATION_BLOCKED_MISSING_SCAFFOLD"


def _task_with_scaffold(tmp_path: Path, agent: str, template: str, status: str = "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION") -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    task = root / "runs" / "tasks" / "task"
    (task / "codex_result").mkdir(exist_ok=True)
    handoff = task / "handoffs" / f"HANDOFF_009_ACOM_RESULT_TO_{agent.upper()}.md"
    handoff.write_text(
        f"---\ndoc_type: handoff\ntask_id: task\nhandoff_id: HANDOFF_009\nfrom_agent: ACOMAgent\nto_agent: {agent}\nfrom_run: RUN_010\ntarget_run: RUN_REVALIDATION_PENDING\nrisk_level: LOW\nexpected_output: trace/RUN_XXX_REVALIDATION.md\n---\n",
        encoding="utf-8",
    )
    structured = empty_structured_result("task", "acom_test")
    structured["tests_run"] = ["pytest -q: passed"]
    structured["artifacts"] = {
        "tests_result": "passed",
        "safety_audit": "passed",
        "secret_audit": "passed",
        "eligibility_gates": ["human approval required"],
    }
    structured["known_limitations"] = ["placeholder result for revalidation unit test"]
    (task / "codex_result" / "structured_result.json").write_text(json.dumps(structured), encoding="utf-8")
    intake = {
        "schema_version": "0.1",
        "task_id": "task",
        "handoff_id": "acom_test",
        "template_id": template,
        "result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        "downstream_agent": agent,
        "result_json": str(task / "codex_result" / "structured_result.json"),
        "downstream_handoff_path": str(handoff),
    }
    (task / "codex_result" / "acom_result_intake.json").write_text(json.dumps(intake), encoding="utf-8")
    scaffold_acom_revalidation(task, downstream_agent=agent, revalidation_id="test")
    scaffold_path = task / "revalidation" / f"{agent}_test" / "REVALIDATION_SCAFFOLD.json"
    if not scaffold_path.exists() and agent in {"ExecutionAgent", "MetricsAgent"}:
        scaffold_path.parent.mkdir(parents=True, exist_ok=True)
        scaffold_path.write_text(json.dumps({
            "schema_version": "0.1",
            "stage": "Stage 5.0E",
            "task_id": "task",
            "task_dir": str(task),
            "status": "REVALIDATION_SCAFFOLD_READY",
            "downstream_agent": agent,
            "revalidation_id": "test",
            "package_dir": str(scaffold_path.parent),
            "acom_intake_path": str(task / "codex_result" / "acom_result_intake.json"),
            "structured_result_path": str(task / "codex_result" / "structured_result.json"),
        }), encoding="utf-8")
    if status != "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION":
        intake["result_status"] = status
        (task / "codex_result" / "acom_result_intake.json").write_text(json.dumps(intake), encoding="utf-8")
    return task
