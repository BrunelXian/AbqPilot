from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_patch_preview_artifacts(artifact_dir: str | Path, payloads: dict[str, Any]) -> dict[str, str]:
    target = Path(artifact_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for name, payload in payloads.items():
        path = target / name
        if isinstance(payload, dict):
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            path.write_text(str(payload), encoding="utf-8")
        paths[path.stem] = str(path)
    return paths


def render_patch_preview_summary(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Guarded Patch Preview",
            "",
            f"Task ID: {summary.get('task_id')}",
            f"Preview status: {summary.get('preview_status')}",
            f"Patch type: {summary.get('patch_type')}",
            f"Source INP: {summary.get('source_inp_path')}",
            f"Candidate INP: {summary.get('candidate_inp_path')}",
            f"Changed lines: {summary.get('changed_lines_count')}",
            f"Unrelated changes: {summary.get('unrelated_changes_count')}",
            "",
            "## Validation",
            "",
            f"- StaticValidator: {summary.get('static_validator_status')}",
            f"- DiffGuard: {summary.get('diff_guard_status')}",
            f"- PhysicsGuard: {summary.get('physics_guard_status')}",
            "",
            "## Safety",
            "",
            f"- Solver submitted: {summary.get('solver_submitted')}",
            f"- Job enqueued: {summary.get('job_enqueued')}",
            f"- Queue runner launched: {summary.get('queue_runner_launched')}",
            f"- ODB opened: {summary.get('opened_odb')}",
            "",
            "## Next Allowed Action",
            "",
            str(summary.get("next_allowed_action")),
            "",
        ]
    )
