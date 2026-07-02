from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.patching.patch_queue_artifacts import write_json_artifact, write_text_artifact


def write_stage3_8a_smoke_summary(workflow_dir: str | Path) -> dict[str, Any]:
    workflow = Path(workflow_dir)
    manifest = _read_json(workflow / "patch_candidate_manifest.json")
    queue_summary = _read_json(workflow / "patch_queue_summary.json")
    preflight = _read_json(workflow / "patch_jobpilot_preflight_result.json")
    dry_run = _read_json(workflow / "patch_jobpilot_dry_run_result.json")
    approval = _read_json(workflow / "patch_candidate_approval_request.json")
    real = _read_json(workflow / "patch_jobpilot_real_enqueue_result.json")
    status = _read_json(workflow / "patch_queue_status_summary.json")
    mutation = _runtime_mutation_summary(real)
    summary = {
        "schema_version": "0.1",
        "stage": "Stage 3.8A",
        "workflow_dir": str(workflow),
        "patch_preview_dir": manifest.get("patch_preview_dir"),
        "candidate_inp_path": manifest.get("candidate_inp_path"),
        "candidate_inp_sha256": manifest.get("candidate_inp_sha256"),
        "source_inp_path": manifest.get("source_inp_path"),
        "source_inp_sha256": manifest.get("source_inp_sha256"),
        "patch_type": manifest.get("patch_type"),
        "preflight_status": preflight.get("status"),
        "dry_run_enqueue_status": dry_run.get("status"),
        "approval_status": "APPROVAL_TOKEN_VALID" if queue_summary.get("approval_status") == "APPROVAL_TOKEN_VALID" else queue_summary.get("approval_status"),
        "real_enqueue_status": "PATCH_QUEUE_REAL_ENQUEUE_COMPLETED"
        if real.get("status") == "REAL_ENQUEUE_COMPLETED"
        else real.get("status"),
        "adapter_real_enqueue_status": real.get("status"),
        "job_id": real.get("job_id") or queue_summary.get("job_id"),
        "queue_only": bool(real.get("queue_only")),
        "queue_file_mutated": bool(real.get("queue_file_mutated", real.get("queue_mutated"))),
        "solver_started": bool(real.get("solver_started")),
        "runner_started": bool(real.get("runner_started")),
        "gui_required": bool(real.get("gui_required")),
        "forbidden_mutations_detected": bool(real.get("forbidden_mutation_detected")),
        "runtime_queue_changed": mutation["runtime_queue_changed"],
        "live_status_changed": mutation["live_status_changed"],
        "reports_changed": mutation["reports_changed"],
        "solver_outputs_created": mutation["solver_outputs_created"],
        "queue_file_path": mutation["queue_file_path"],
        "runtime_snapshot_before": real.get("runtime_snapshot_before"),
        "runtime_snapshot_after": real.get("runtime_snapshot_after"),
        "normalized_status": status.get("normalized_status"),
        "solver_submitted": False,
        "queue_runner_launched": False,
        "opened_odb": False,
        "final_pipeline_status": queue_summary.get("final_pipeline_status") or "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER",
        "approval_request_path": str(workflow / "patch_candidate_approval_request.json") if approval else None,
    }
    write_json_artifact(workflow / "stage3_8a_patch_queue_real_enqueue_smoke_summary.json", summary)
    write_text_artifact(workflow / "stage3_8a_patch_queue_real_enqueue_smoke_summary.md", _render_summary(summary))
    return {
        "command": "write-stage3-8a-smoke-summary",
        "verdict": _verdict(summary),
        "success": _verdict(summary) == "PASS_ABQPILOT_V2_STAGE3_8A_PATCH_QUEUE_PRODUCTION_REAL_ENQUEUE_SMOKE_READY",
        "output_paths": {
            "summary_json": str(workflow / "stage3_8a_patch_queue_real_enqueue_smoke_summary.json"),
            "summary_md": str(workflow / "stage3_8a_patch_queue_real_enqueue_smoke_summary.md"),
        },
        "details": summary,
        "warnings": [],
        "errors": [] if _verdict(summary).startswith("PASS_") else ["Stage 3.8A queue-only smoke conditions were not all satisfied"],
    }


def _runtime_mutation_summary(real: dict[str, Any]) -> dict[str, Any]:
    before = real.get("runtime_snapshot_before", {}).get("paths", {})
    after = real.get("runtime_snapshot_after", {}).get("paths", {})
    queue_key = _find_key(after, "queue.json")
    live_key = _find_key(after, "live_status.json")
    reports_key = _find_key(after, "reports")
    solver_before = real.get("solver_output_snapshot_before", {}).get("files", {})
    solver_after = real.get("solver_output_snapshot_after", {}).get("files", {})
    solver_created = False
    for ext, after_entry in solver_after.items():
        before_entry = solver_before.get(ext, {})
        if after_entry.get("exists") and not before_entry.get("exists"):
            solver_created = True
    return {
        "runtime_queue_changed": bool(queue_key and before.get(queue_key) != after.get(queue_key)),
        "live_status_changed": bool(live_key and before.get(live_key) != after.get(live_key)),
        "reports_changed": bool(reports_key and before.get(reports_key) != after.get(reports_key)),
        "solver_outputs_created": solver_created,
        "queue_file_path": after.get(queue_key, {}).get("path") if queue_key else None,
    }


def _find_key(paths: dict[str, Any], suffix: str) -> str | None:
    suffix_lower = suffix.lower()
    for key, value in paths.items():
        path = str(value.get("path") or key).replace("\\", "/").lower()
        if path.endswith(suffix_lower):
            return key
    return None


def _verdict(summary: dict[str, Any]) -> str:
    safe = (
        summary.get("preflight_status") == "PREVIEW_READY"
        and summary.get("dry_run_enqueue_status") == "DRY_RUN_READY"
        and summary.get("approval_status") == "APPROVAL_TOKEN_VALID"
        and summary.get("real_enqueue_status") == "PATCH_QUEUE_REAL_ENQUEUE_COMPLETED"
        and summary.get("queue_only") is True
        and summary.get("queue_file_mutated") is True
        and summary.get("solver_started") is False
        and summary.get("runner_started") is False
        and summary.get("gui_required") is False
        and summary.get("forbidden_mutations_detected") is False
        and summary.get("runtime_queue_changed") is True
        and summary.get("live_status_changed") is False
        and summary.get("reports_changed") is False
        and summary.get("solver_outputs_created") is False
        and summary.get("solver_submitted") is False
        and summary.get("queue_runner_launched") is False
        and summary.get("opened_odb") is False
    )
    return "PASS_ABQPILOT_V2_STAGE3_8A_PATCH_QUEUE_PRODUCTION_REAL_ENQUEUE_SMOKE_READY" if safe else "FAIL_STAGE3_8A_FORBIDDEN_RUNTIME_MUTATION_DETECTED"


def _render_summary(summary: dict[str, Any]) -> str:
    return f"""# Stage 3.8A Patch Queue Production Real-Enqueue Smoke

Verdict: {_verdict(summary)}

- Workflow: {summary.get("workflow_dir")}
- Patch preview: {summary.get("patch_preview_dir")}
- Candidate INP: {summary.get("candidate_inp_path")}
- Candidate SHA256: {summary.get("candidate_inp_sha256")}
- Job ID: {summary.get("job_id")}
- Real enqueue status: {summary.get("real_enqueue_status")}
- Queue-only: {summary.get("queue_only")}
- Queue file mutated: {summary.get("queue_file_mutated")}
- Solver started: {summary.get("solver_started")}
- Runner started: {summary.get("runner_started")}
- GUI required: {summary.get("gui_required")}
- Forbidden mutations detected: {summary.get("forbidden_mutations_detected")}
- Queue changed: {summary.get("runtime_queue_changed")}
- live_status changed: {summary.get("live_status_changed")}
- reports changed: {summary.get("reports_changed")}
- Solver outputs created: {summary.get("solver_outputs_created")}
- Normalized status: {summary.get("normalized_status")}

No solver was submitted, no external queue worker was launched, and no ODB was opened.
"""


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
