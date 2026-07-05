from __future__ import annotations

import json
from pathlib import Path

from abqpilot import cli
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_cli_generate_and_report_non_solver_evidence_summary(tmp_path):
    task = _task(tmp_path)
    _write_ledger(task)
    result = cli.command_generate_non_solver_evidence_summary(task)
    assert result["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_READY"
    report = cli.command_report_non_solver_evidence_summary(task)
    assert report["verdict"] == "NON_SOLVER_EVIDENCE_SUMMARY_REPORT_READY"
    assert Path(report["output_paths"]["report_path"]).exists()


def _task(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    scaffold_pipeline_task("task", root=root)
    return root / "runs" / "tasks" / "task"


def _write_ledger(task: Path) -> None:
    task.joinpath("NON_SOLVER_EVIDENCE_LEDGER.md").write_text("# Non-Solver Evidence Ledger\n\nNon-final.\n", encoding="utf-8")
    task.joinpath("NON_SOLVER_EVIDENCE_LEDGER.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "ledger_type": "non_solver_evidence",
                "entries": [
                    {
                        "task_id": "task",
                        "source_revalidation_agent": "DocsStatusAgent",
                        "source_revalidation_status": "NON_SOLVER_REVALIDATION_PASS_PENDING_SUPERVISOR",
                        "supervisor_review_status": "SUPERVISOR_NON_SOLVER_REVIEW_ACCEPTED_FOR_LEDGER",
                        "ledger_decision": "ACCEPTED_FOR_NON_SOLVER_EVIDENCE_LEDGER",
                        "artifacts_reviewed": [],
                        "final_evidence_approved": False,
                        "final_verdict_frozen": False,
                        "solver_approved": False,
                        "odb_metrics_approved": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
