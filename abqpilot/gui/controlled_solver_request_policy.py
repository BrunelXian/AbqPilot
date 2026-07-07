from __future__ import annotations

from pathlib import Path
from typing import Any


ACCEPTABLE_SOLVER_COMMAND_LABELS = {
    "ABAQUS_2024_CONFIGURED_BUT_NOT_INVOKED",
    "CONTROLLED_ABAQUS_SOLVER_FUTURE_STAGE",
    "ABQ2024_FUTURE_CONTROLLED_SOLVER_STAGE",
}

RESOURCE_POLICY_DEFAULTS = {
    "cpu_count_preview": "FUTURE_STAGE_POLICY",
    "memory_policy_preview": "FUTURE_STAGE_POLICY",
    "timeout_policy_preview": "FUTURE_STAGE_POLICY",
    "log_capture_policy_preview": "FUTURE_STAGE_POLICY",
}


def validate_solver_command_label_policy(label: str | None, solver_command_path_included: bool, solver_command_not_invoked: bool) -> dict[str, Any]:
    forbidden_fragments = ("\\", "/", ".bat", ".cmd", " ", "&&", "|", ";")
    label_present = bool(label)
    label_is_known = label in ACCEPTABLE_SOLVER_COMMAND_LABELS
    label_is_not_shell_command = label_present and not any(fragment in str(label).lower() for fragment in forbidden_fragments)
    ok = label_present and label_is_known and label_is_not_shell_command and solver_command_path_included is False and solver_command_not_invoked is True
    return {
        "policy_status": "SOLVER_COMMAND_LABEL_POLICY_VALID" if ok else "SOLVER_COMMAND_LABEL_POLICY_BLOCKED",
        "solver_command_label": label,
        "solver_command_label_validated": ok,
        "solver_command_path_not_invoked": solver_command_not_invoked is True,
        "solver_command_path_included": solver_command_path_included is True,
        "label_is_known": label_is_known,
        "label_is_not_shell_command": label_is_not_shell_command,
    }


def validate_output_dir_policy(path_value: str | None, task_dir: str | Path, output_dir_created: bool, forbidden_root: str | Path = r"D:\Users\wuxia\Documents\AbqPilot") -> dict[str, Any]:
    task = Path(task_dir)
    forbidden = Path(forbidden_root)
    if not path_value:
        return _output_result(path_value, False, "missing output directory preview")
    candidate = Path(path_value)
    resolved = candidate if candidate.is_absolute() else task / candidate
    resolved_text = str(resolved)
    task_text = str(task)
    forbidden_text = str(forbidden)
    parts = {part.lower() for part in resolved.parts}
    under_task = resolved_text.lower().startswith(task_text.lower())
    under_forbidden = resolved_text.lower().startswith(forbidden_text.lower())
    queue_runtime_status = bool({"queue", "runtime", "status"} & parts) or resolved.name.lower() in {"queue.json", "live_status.json"}
    source_model = "source" in parts and ("sanity" in resolved_text.lower() or "base" in resolved_text.lower())
    ok = under_task and not under_forbidden and not queue_runtime_status and not source_model and output_dir_created is False and not resolved.exists()
    reason = None if ok else "output directory preview violates Stage 5.2I policy"
    return _output_result(path_value, ok, reason, resolved)


def validate_resource_policy_shape(request_draft: dict[str, Any]) -> dict[str, Any]:
    values = {key: request_draft.get(key, default) for key, default in RESOURCE_POLICY_DEFAULTS.items()}
    ok = all(value not in (None, "") for value in values.values())
    return {
        "policy_status": "RESOURCE_POLICY_SHAPE_VALID" if ok else "RESOURCE_POLICY_SHAPE_BLOCKED",
        "cpu_policy_validated": bool(values["cpu_count_preview"]),
        "memory_policy_validated": bool(values["memory_policy_preview"]),
        "timeout_policy_validated": bool(values["timeout_policy_preview"]),
        "log_capture_policy_validated": bool(values["log_capture_policy_preview"]),
        **values,
    }


def _output_result(path_value: str | None, ok: bool, reason: str | None, resolved: Path | None = None) -> dict[str, Any]:
    return {
        "policy_status": "OUTPUT_DIR_POLICY_VALID" if ok else "OUTPUT_DIR_POLICY_BLOCKED",
        "allowed_output_dir_preview": path_value,
        "resolved_output_dir_preview": str(resolved) if resolved else None,
        "output_dir_policy_validated": ok,
        "output_dir_created": False,
        "blocked_reason": reason,
    }
