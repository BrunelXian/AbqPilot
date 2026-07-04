from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.revalidation_scaffold import scaffold_acom_revalidation
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_accepted_acom_intake_produces_revalidation_scaffold(tmp_path):
    task = _task_with_intake(tmp_path, "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION")
    result = scaffold_acom_revalidation(task, revalidation_id="test")
    assert result["verdict"] == "REVALIDATION_SCAFFOLD_READY"
    details = result["details"]
    package = Path(details["package_dir"])
    assert (package / "REVALIDATION_PLAN.md").exists()
    assert (package / "REVALIDATION_CHECKLIST.md").exists()
    assert (package / "REVALIDATION_EXPECTED_OUTPUTS.md").exists()
    assert (package / "REVALIDATION_SCAFFOLD.json").exists()
    assert (package / "REVALIDATION_REPORT.md").exists()
    gate_fm = load_frontmatter(details["gate_path"])
    assert gate_fm["decision"] == "PENDING_REVALIDATION"
    assert gate_fm["decision"] != "APPROVED"
    assert gate_fm["automatic_execution_performed"] is False
    run_fm = load_frontmatter(details["run_record_path"])
    assert run_fm["doc_type"] == "run_report"
    handoff_fm = load_frontmatter(details["handoff_path"])
    assert handoff_fm["to_agent"] == "PipelineSupervisor"
    assert validate_task_protocol(task)["verdict"] == "PIPELINE_PROTOCOL_VALID"


def test_rejected_acom_intake_blocks_scaffold(tmp_path):
    task = _task_with_intake(tmp_path, "ACOM_RESULT_REJECTED_SAFETY_FLAGS")
    result = scaffold_acom_revalidation(task, revalidation_id="test")
    assert result["verdict"] == "REVALIDATION_SCAFFOLD_BLOCKED_ACOM_RESULT_NOT_ACCEPTED"
    assert not (task / "revalidation").exists()


def test_missing_acom_intake_blocks_scaffold(tmp_path):
    task = _base_task(tmp_path)
    result = scaffold_acom_revalidation(task)
    assert result["verdict"] == "REVALIDATION_SCAFFOLD_BLOCKED_MISSING_ACOM_INTAKE"


def test_unknown_downstream_agent_blocks_scaffold(tmp_path):
    task = _task_with_intake(tmp_path, "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION", downstream="UnknownAgent", template="unknown_template")
    result = scaffold_acom_revalidation(task)
    assert result["verdict"] == "REVALIDATION_SCAFFOLD_BLOCKED_UNKNOWN_DOWNSTREAM_AGENT"


def _base_task(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    return root / "runs" / "tasks" / "task"


def _task_with_intake(
    tmp_path: Path,
    status: str,
    downstream: str = "GuardAgent",
    template: str = "mcpguard_review",
) -> Path:
    task = _base_task(tmp_path)
    handoff = task / "handoffs" / "HANDOFF_009_ACOM_RESULT_TO_GUARD_AGENT.md"
    handoff.write_text("---\ndoc_type: handoff\ntask_id: task\nhandoff_id: HANDOFF_009\nfrom_agent: ACOMAgent\nto_agent: GuardAgent\nfrom_run: RUN_010\ntarget_run: RUN_REVALIDATION_PENDING\nrisk_level: MEDIUM\nexpected_output: trace/RUN_XXX_GUARD_REVALIDATION.md\n---\n", encoding="utf-8")
    (task / "codex_result").mkdir(exist_ok=True)
    payload = {
        "schema_version": "0.1",
        "task_id": "task",
        "handoff_id": "acom_test",
        "template_id": template,
        "result_status": status,
        "downstream_agent": downstream,
        "result_json": str(task / "codex_result" / "structured_result.json"),
        "downstream_handoff_path": str(handoff),
    }
    (task / "codex_result" / "acom_result_intake.json").write_text(json.dumps(payload), encoding="utf-8")
    return task
