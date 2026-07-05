from __future__ import annotations

import json
from pathlib import Path

from abqpilot import cli
from abqpilot.acom.non_solver_evidence_summary import generate_non_solver_evidence_summary
from abqpilot.pipeline_protocol.task_scaffold import scaffold_pipeline_task


def test_cli_supervisor_ack_non_solver_summary_and_report(tmp_path):
    task = _task(tmp_path)
    _write_ledger(task)
    generate_non_solver_evidence_summary(task)
    result = cli.command_supervisor_ack_non_solver_summary(task)
    assert result["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_ACCEPTED"
    report = cli.command_report_supervisor_non_solver_summary_ack(task)
    assert report["verdict"] == "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_REPORT_READY"
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
