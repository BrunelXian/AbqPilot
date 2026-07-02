from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_artifact(path: str | Path, payload: dict[str, Any]) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(target)


def write_text_artifact(path: str | Path, text: str) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return str(target)


def render_patch_queue_summary(summary: dict[str, Any]) -> str:
    return f"""# Patch-to-Queue Workflow

Status: {summary.get("workflow_status")}

## Candidate

- Patch type: {summary.get("patch_type")}
- Candidate INP: {summary.get("candidate_inp_path")}
- Candidate SHA256: {summary.get("candidate_inp_sha256")}
- StaticValidator: {summary.get("static_validator_status")}
- DiffGuard: {summary.get("diff_guard_status")}
- PhysicsGuard: {summary.get("physics_guard_status")}

## JobPilot

- Preflight: {summary.get("preflight_status")}
- Dry-run enqueue: {summary.get("dry_run_enqueue_status")}
- Approval: {summary.get("approval_status")}
- Real queue enqueue: {summary.get("real_enqueue_status")}
- Job ID: {summary.get("job_id")}
- Normalized status: {summary.get("normalized_status")}

## Safety

- Solver submitted: {summary.get("solver_submitted")}
- Queue runner launched: {summary.get("queue_runner_launched")}
- ODB opened: {summary.get("opened_odb")}
- LLM executed action: {summary.get("llm_executed_action")}
"""


def render_patch_approval_request(request: dict[str, Any]) -> str:
    return f"""# Patch Candidate Queue Approval Request

Status: {request.get("status")}

This request binds a validated patch preview candidate to a future queue-only enqueue.

- Parent task: {request.get("parent_task_id")}
- Patch type: {request.get("patch_type")}
- Candidate SHA256: {request.get("candidate_inp_sha256")}
- Changed lines: {request.get("changed_lines_count")}
- Unrelated changes: {request.get("unrelated_changes_count")}

No job was enqueued by creating this request. No solver was submitted.
"""
