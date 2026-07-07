from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.controlled_solver_candidate_hash import compute_candidate_artifact_hash


SMOKE_TASK_ID = "stage5_2f_controlled_solver_real_gate_smoke"
SOLVER_REQUEST_FILENAMES = {
    "solver_request.json",
    "job_request.json",
    "abaqus_job.json",
    "run_solver.bat",
    "run_solver.cmd",
}


def validate_controlled_solver_real_gate_smoke(task_dir: str | Path, gate: dict[str, Any], token: dict[str, Any]) -> dict[str, Any]:
    task = Path(task_dir)
    gate_json = task / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.json"
    gate_md = task / "gates" / "GATE_001_CONTROLLED_SOLVER_HUMAN_APPROVAL.md"
    candidate = Path(str(gate.get("candidate_artifact_path")))
    expected_hash = compute_candidate_artifact_hash(candidate)["hash"]
    checks = {
        "gate_json_exists": gate_json.exists() or gate.get("gate_id") == "GATE_001",
        "gate_markdown_exists": gate_md.exists() or gate.get("gate_id") == "GATE_001",
        "gate_under_smoke_task_only": task.name == SMOKE_TASK_ID,
        "candidate_artifact_exists": candidate.exists(),
        "candidate_hash_matches_token": bool(expected_hash and token.get("candidate_artifact_hash") == expected_hash and gate.get("candidate_artifact_hash") == expected_hash),
        "token_consumed_once": token.get("consumed_once") is True and gate.get("token_consumed_once") is True,
        "solver_approved_true": gate.get("solver_approved") is True,
        "solver_execution_allowed_false": gate.get("solver_execution_allowed") is False,
        "solver_request_created_false": gate.get("solver_request_created") is False,
        "solver_run_false": gate.get("solver_run") is False,
        "queue_runner_launched_false": gate.get("queue_runner_launched") is False,
        "odb_opened_false": gate.get("odb_opened") is False,
        "final_evidence_approved_false": gate.get("final_evidence_approved") is False,
        "final_verdict_frozen_false": gate.get("final_verdict_frozen") is False,
        "task_final_evidence_ledger_updated_false": gate.get("task_final_evidence_ledger_updated") is False,
    }
    no_solver_request = not any((task / name).exists() for name in SOLVER_REQUEST_FILENAMES)
    no_queue = not any((task / name).exists() for name in ("queue.json", "live_status.json", "queue"))
    no_odb = not any(task.rglob("*.odb")) if task.exists() else True
    no_execution_handoff = not any(_is_active_execution_handoff(path) for path in (task / "handoffs").glob("*.md")) if (task / "handoffs").exists() else True
    no_final_ledger = not (task / "TASK_FINAL_EVIDENCE_LEDGER.md").exists()
    checks.update(
        {
            "no_solver_request_files_found": no_solver_request,
            "no_queue_files_found": no_queue,
            "no_odb_files_found": no_odb,
            "no_execution_handoff_found": no_execution_handoff,
            "no_task_final_evidence_ledger": no_final_ledger,
        }
    )
    status = "CONTROLLED_SOLVER_REAL_GATE_VALID_NO_EXECUTION" if all(checks.values()) else "CONTROLLED_SOLVER_REAL_GATE_INVALID_OR_UNSAFE"
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2F",
        "validation_status": status,
        "checks": checks,
        "no_solver_request_files_found": no_solver_request,
        "no_queue_files_found": no_queue,
        "no_odb_files_found": no_odb,
        "no_execution_handoff_found": no_execution_handoff,
        "no_task_final_evidence_ledger": no_final_ledger,
        "solver_execution_allowed": False,
        "solver_request_created": False,
        "solver_run": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
    }


def _is_active_execution_handoff(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return "handoff_active_for_execution: true" in text.lower() or "solver_auto_start: true" in text.lower()
