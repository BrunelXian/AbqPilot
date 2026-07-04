from __future__ import annotations

import json
from pathlib import Path

from abqpilot import cli
from abqpilot.acom.result_schema import empty_structured_result
from abqpilot.acom.revalidation_scaffold import scaffold_acom_revalidation
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_cli_execute_and_report_non_solver_revalidation(tmp_path):
    task = _task(tmp_path)
    result = cli.command_execute_non_solver_revalidation(task)
    assert result["verdict"] == "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR"
    report = cli.command_report_non_solver_revalidation(task)
    assert report["verdict"] == "NON_SOLVER_REVALIDATION_REPORT_READY"


def _task(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    task = root / "runs" / "tasks" / "task"
    (task / "codex_result").mkdir(exist_ok=True)
    handoff = task / "handoffs" / "HANDOFF_009_ACOM_RESULT_TO_DOCS_STATUS_AGENT.md"
    handoff.write_text("---\ndoc_type: handoff\ntask_id: task\nhandoff_id: HANDOFF_009\nfrom_agent: ACOMAgent\nto_agent: DocsStatusAgent\nfrom_run: RUN_010\ntarget_run: RUN_REVALIDATION_PENDING\nrisk_level: LOW\nexpected_output: trace/RUN_XXX_REVALIDATION.md\n---\n", encoding="utf-8")
    structured = empty_structured_result("task", "acom_test")
    structured["known_limitations"] = ["unit test"]
    (task / "codex_result" / "structured_result.json").write_text(json.dumps(structured), encoding="utf-8")
    (task / "codex_result" / "acom_result_intake.json").write_text(json.dumps({
        "task_id": "task",
        "handoff_id": "acom_test",
        "template_id": "docs_status_update",
        "result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        "downstream_agent": "DocsStatusAgent",
        "result_json": str(task / "codex_result" / "structured_result.json"),
        "downstream_handoff_path": str(handoff),
    }), encoding="utf-8")
    scaffold_acom_revalidation(task, downstream_agent="DocsStatusAgent", revalidation_id="cli")
    return task
