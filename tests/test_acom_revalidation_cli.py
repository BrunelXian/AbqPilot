from __future__ import annotations

import json

from abqpilot import cli
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_cli_scaffold_and_report_acom_revalidation(tmp_path):
    task = _task(tmp_path)
    result = cli.command_scaffold_acom_revalidation(task, revalidation_id="cli")
    assert result["verdict"] == "REVALIDATION_SCAFFOLD_READY"
    report = cli.command_report_acom_revalidation(task, revalidation_id="cli")
    assert report["verdict"] == "ACOM_REVALIDATION_REPORT_READY"


def _task(tmp_path):
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    task = root / "runs" / "tasks" / "task"
    handoff = task / "handoffs" / "HANDOFF_009_ACOM_RESULT_TO_GUARD_AGENT.md"
    handoff.write_text("---\ndoc_type: handoff\ntask_id: task\nhandoff_id: HANDOFF_009\nfrom_agent: ACOMAgent\nto_agent: GuardAgent\nfrom_run: RUN_010\ntarget_run: RUN_REVALIDATION_PENDING\nrisk_level: MEDIUM\nexpected_output: trace/RUN_XXX_GUARD_REVALIDATION.md\n---\n", encoding="utf-8")
    (task / "codex_result").mkdir(exist_ok=True)
    (task / "codex_result" / "acom_result_intake.json").write_text(json.dumps({
        "task_id": "task",
        "template_id": "mcpguard_review",
        "result_status": "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION",
        "downstream_agent": "GuardAgent",
        "result_json": str(task / "codex_result" / "structured_result.json"),
        "downstream_handoff_path": str(handoff),
    }), encoding="utf-8")
    return task
