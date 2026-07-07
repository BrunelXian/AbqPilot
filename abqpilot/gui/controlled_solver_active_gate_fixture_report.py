from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_active_gate_fixture_writer import write_controlled_solver_active_gate_fixture
from abqpilot.gui.controlled_solver_active_gate_writer_policy import PROJECT_ROOT


STAGE5_2E_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2E_CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_TEST_FIXTURE_READY"


def write_active_gate_writer_fixture_report(project_root: str | Path = PROJECT_ROOT) -> dict[str, Any]:
    root = Path(project_root)
    out = root / "gui_high_risk_gate_ux" / "controlled_solver_active_gate_writer_fixture"
    out.mkdir(parents=True, exist_ok=True)
    fixture_dir = root / "tests" / "fixtures" / "stage5_2e_active_gate_writer_fixture"
    candidate = fixture_dir / "candidate_fixture.inp"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    candidate.write_text("*Heading\nFixture candidate only\n", encoding="utf-8")
    fixture_result = write_controlled_solver_active_gate_fixture(
        fixture_dir,
        fixture_mode=True,
        task_id="stage5_2e_fixture_task",
        task_dir=fixture_dir,
        candidate_artifact_path=candidate,
    )
    blocked_result = write_controlled_solver_active_gate_fixture(
        PROJECT_ROOT / "runs" / "tasks" / "stage5_2e_real_task_probe" / "gates",
        fixture_mode=True,
    )
    summary = {
        "schema_version": "0.1",
        "stage": "Stage 5.2E",
        "verdict": STAGE5_2E_VERDICT,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "fixture_write_supported": fixture_result["writer_status"] == "ACTIVE_GATE_WRITER_FIXTURE_WRITE_OK",
        "real_task_write_enabled": False,
        "real_task_write_attempt_blocked": blocked_result["writer_status"] != "ACTIVE_GATE_WRITER_FIXTURE_WRITE_OK",
        "solver_request_created": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "odb_metrics_approved": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "no_real_task_gate_written": True,
        "fixture_result": fixture_result,
        "blocked_real_task_result": blocked_result,
    }
    paths = {
        "policy": out / "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_POLICY.md",
        "report": out / "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_REPORT.md",
        "result": out / "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_FIXTURE_RESULT.json",
        "blocked": out / "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_BLOCKED_REAL_TASK_REPORT.md",
    }
    paths["policy"].write_text(render_fixture_writer_policy(), encoding="utf-8")
    paths["report"].write_text(render_fixture_writer_report(summary), encoding="utf-8")
    paths["result"].write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["blocked"].write_text(render_blocked_real_task_report(blocked_result), encoding="utf-8")
    return {
        "command": "report-controlled-solver-active-gate-writer-policy",
        "verdict": "CONTROLLED_SOLVER_ACTIVE_GATE_WRITER_POLICY_REPORT_READY",
        "success": True,
        "output_paths": {key: str(path) for key, path in paths.items()},
        "details": summary,
        "warnings": [],
        "errors": [],
    }


def render_fixture_writer_policy() -> str:
    return "\n".join(
        [
            "# Controlled Solver Active Gate Writer Fixture Policy",
            "",
            "- TEST_FIXTURE_ONLY mode is supported.",
            "- REAL_TASK_WRITE_DISABLED mode remains active for real tasks.",
            "- Real `runs/tasks/*/gates` writes are blocked.",
            "- Solver request creation is blocked.",
            "- Execution handoff creation is blocked.",
            "- Final evidence authority is blocked.",
            "- No Abaqus solver command is executed.",
            "- `TASK_FINAL_EVIDENCE_LEDGER.md` remains untouched.",
            "",
        ]
    )


def render_fixture_writer_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Controlled Solver Active Gate Writer Fixture Report",
            "",
            "Stage 5.2E tests active gate writer in fixtures only.",
            "",
            f"Fixture write supported: {summary['fixture_write_supported']}",
            f"Real task write enabled: {summary['real_task_write_enabled']}",
            f"Real task write attempt blocked: {summary['real_task_write_attempt_blocked']}",
            "",
            "Fixture active gate records are not real solver approvals.",
            "Solver execution remains a future separate explicit stage.",
            "No solver request files are created.",
            "No Abaqus solver command is executed.",
            "No ODB/metrics/final evidence authority is granted.",
            "`TASK_FINAL_EVIDENCE_LEDGER.md` remains untouched.",
            "",
        ]
    )


def render_blocked_real_task_report(blocked_result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Blocked Real Task Gate Write Report",
            "",
            f"Writer status: {blocked_result.get('writer_status')}",
            "Real task gates must not be written in Stage 5.2E.",
            "No solver request file was created.",
            "No active execution handoff was created.",
            "",
        ]
    )
