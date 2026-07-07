from __future__ import annotations

from pathlib import Path
from typing import Any

TASK_ID = "stage5_3a_v2_controlled_solver_demo_smoke"
FORBIDDEN_ROOT = Path(r"D:\Users\wuxia\Documents\AbqPilot")
STAGE5_3A_MARKERS = ["STAGE5_3A", "Stage 5.3A", "controlled_solver_demo_smoke", "CONTROLLED_SOLVER_DEMO", "test_controlled_solver_demo_smoke"]


def scan_forbidden_root_for_stage5_3a_markers(forbidden_root: str | Path = FORBIDDEN_ROOT) -> list[str]:
    root = Path(forbidden_root)
    if not root.exists():
        return []
    hits: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        path_hit = any(marker in str(path) for marker in STAGE5_3A_MARKERS)
        content_hit = False
        try:
            content_hit = any(marker in path.read_text(encoding="utf-8", errors="ignore") for marker in STAGE5_3A_MARKERS)
        except OSError:
            content_hit = False
        if path_hit or content_hit:
            hits.append(str(path))
    return hits


def audit_stage5_3a_v2_no_forbidden_outputs(project_root: str | Path, status: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(project_root)
    task = root / "runs" / "tasks" / TASK_ID
    solver_requests = sorted(str(p) for p in root.rglob("solver_request.json") if p.is_file())
    allowed_request = str(task / "artifacts" / "solver_requests" / "solver_request.json")
    checks = {
        "solver_request_only_under_stage5_3a_v2": solver_requests == [allowed_request],
        "no_job_request_json": not list(task.rglob("job_request.json")) if task.exists() else True,
        "no_abaqus_job_json": not list(task.rglob("abaqus_job.json")) if task.exists() else True,
        "no_queue_files": not [p for p in task.rglob("*") if p.name.lower() in {"queue.json", "live_status.json"}] if task.exists() else True,
        "no_metrics_files": not [p for p in task.rglob("*metrics*") if p.is_file()] if task.exists() else True,
        "no_task_final_evidence_ledger": not (root / "TASK_FINAL_EVIDENCE_LEDGER.md").exists(),
        "odb_not_opened": (status or {}).get("odb_opened") is not True,
        "metrics_not_extracted": (status or {}).get("metrics_extracted") is not True,
        "final_evidence_not_approved": (status or {}).get("final_evidence_approved") is not True,
        "forbidden_root_stage5_3a_scan_clean": not scan_forbidden_root_for_stage5_3a_markers(),
    }
    return {"audit_status": "STAGE5_3A_V2_SAFETY_AUDIT_PASS" if all(checks.values()) else "STAGE5_3A_V2_SAFETY_AUDIT_FAIL", "checks": checks, "solver_request_paths": solver_requests, "allowed_solver_request_path": allowed_request, "forbidden_root_hits": scan_forbidden_root_for_stage5_3a_markers()}
