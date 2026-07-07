from __future__ import annotations

from pathlib import Path
from typing import Any


TASK_ID = "stage5_3a_controlled_solver_demo_smoke"
READY = "STAGE5_3A_DEMO_SOLVER_REQUEST_VALID"


def validate_demo_gate(gate: dict[str, Any]) -> dict[str, Any]:
    required = {
        "doc_type": "gate_decision",
        "gate_type": "CONTROLLED_SOLVER_DEMO_RUN",
        "stage_id": "STAGE5_3A",
        "task_id": TASK_ID,
        "smoke_demo_only": True,
        "arbitrary_task_execution_allowed": False,
        "decision": "APPROVED_BY_HUMAN_FOR_DEMO_SMOKE_RUN",
        "solver_execution_allowed": True,
        "solver_execution_scope": "STAGE5_3A_DEMO_SMOKE_ONLY",
        "solver_request_created": True,
        "queue_runner_allowed": False,
        "queue_runner_launched": False,
        "odb_open_allowed": False,
        "odb_opened": False,
        "metrics_extraction_allowed": False,
        "metrics_extracted": False,
        "metrics_approved": False,
        "final_evidence_approval_allowed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "abaqus_command_invocation_allowed": True,
        "one_solver_run_only": True,
        "run_count_limit": 1,
    }
    checks = {f"{key}_ok": gate.get(key) == value for key, value in required.items()}
    return {"validation_status": "STAGE5_3A_DEMO_GATE_VALID" if all(checks.values()) else "STAGE5_3A_DEMO_GATE_INVALID", "checks": checks}


def validate_demo_solver_request(request: dict[str, Any]) -> dict[str, Any]:
    required = {
        "request_type": "CONTROLLED_SOLVER_DEMO_SMOKE_RUN",
        "stage_id": "STAGE5_3A",
        "task_id": TASK_ID,
        "smoke_demo_only": True,
        "active_request": True,
        "executable_request": True,
        "arbitrary_task_execution_allowed": False,
        "source_gate_id": "GATE_001",
        "source_gate_validated": True,
        "candidate_hash_verified": True,
        "solver_command_label": "ABAQUS_2024_CONTROLLED_DEMO",
        "solver_command_path": r"D:\ABAQUS2024\Commands\abq2024.bat",
        "solver_command_invocation_allowed": True,
        "solver_execution_allowed": True,
        "queue_runner_allowed": False,
        "queue_runner_launched": False,
        "queue_entry_created": False,
        "odb_open_allowed": False,
        "odb_opened": False,
        "metrics_extraction_allowed": False,
        "metrics_extracted": False,
        "metrics_approved": False,
        "final_evidence_approval_allowed": False,
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "task_final_evidence_ledger_updated": False,
        "capture_stdout": True,
        "capture_stderr": True,
    }
    checks = {f"{key}_ok": request.get(key) == value for key, value in required.items()}
    checks["cpu_count_bounded_ok"] = 1 <= int(request.get("cpu_count", 0)) <= 14
    checks["candidate_exists_ok"] = Path(str(request.get("candidate_inp_path", ""))).exists()
    checks["working_directory_under_task_ok"] = TASK_ID in str(request.get("working_directory", ""))
    return {"validation_status": READY if all(checks.values()) else "STAGE5_3A_DEMO_SOLVER_REQUEST_INVALID", "checks": checks}
