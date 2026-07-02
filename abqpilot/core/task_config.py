from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_TASK_CONFIG: dict[str, Any] = {
    "task_name": "abqpilot_task",
    "cae_path": None,
    "work_root": "runs",
    "abaqus_command": "disabled",
    "allow_cae_export": False,
    "cae_export_mode": "write_input_only",
    "allow_odb_read": False,
    "odb_read_mode": "disabled",
    "allow_solver_submit": False,
    "allow_abqjobpilot": False,
    "allow_abqjobpilot_preflight": False,
    "allow_abqjobpilot_dry_run_enqueue": False,
    "allow_jobpilot_enqueue_authorization": False,
    "allow_abqjobpilot_real_enqueue": False,
    "allow_abqjobpilot_status_poll": False,
    "allow_llm": False,
    "allow_cae_modify": False,
    "heat_input_scale": 2.0,
}


class TaskConfigError(ValueError):
    """Raised when a task config violates AbqPilot safety boundaries."""


def load_task_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_TASK_CONFIG)
    if path is not None:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Task config does not exist: {config_path}")
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise TaskConfigError("Task config JSON must contain an object")
        config.update(loaded)

    if overrides:
        config.update({key: value for key, value in overrides.items() if value is not None})

    return validate_task_config(config)


def validate_task_config(config: dict[str, Any]) -> dict[str, Any]:
    validated = dict(config)
    _require_bool(validated, "allow_cae_export")
    _require_bool(validated, "allow_odb_read")
    _require_bool(validated, "allow_solver_submit")
    _require_bool(validated, "allow_abqjobpilot")
    _require_bool(validated, "allow_abqjobpilot_preflight")
    _require_bool(validated, "allow_abqjobpilot_dry_run_enqueue")
    _require_bool(validated, "allow_jobpilot_enqueue_authorization")
    _require_bool(validated, "allow_abqjobpilot_real_enqueue")
    _require_bool(validated, "allow_abqjobpilot_status_poll")
    _require_bool(validated, "allow_llm")
    _require_bool(validated, "allow_cae_modify")

    if validated["allow_solver_submit"] is not False:
        raise TaskConfigError("allow_solver_submit must be false for Stage 2.0 CLI")
    if validated["allow_abqjobpilot"] is not False:
        raise TaskConfigError("allow_abqjobpilot must be false for Stage 2.0 CLI")
    if validated["allow_llm"] is not False:
        raise TaskConfigError("allow_llm must be false for Stage 2.0 CLI")
    if validated["allow_cae_modify"] is not False:
        raise TaskConfigError("allow_cae_modify must be false for Stage 2.0 CLI")

    if validated.get("allow_cae_export") and validated.get("cae_export_mode") != "write_input_only":
        raise TaskConfigError("cae_export_mode must be write_input_only when CAE export is enabled")
    if validated.get("allow_odb_read") and validated.get("odb_read_mode") != "metrics_only":
        raise TaskConfigError("odb_read_mode must be metrics_only when ODB read is enabled")

    try:
        scale = float(validated.get("heat_input_scale", 2.0))
    except (TypeError, ValueError) as exc:
        raise TaskConfigError("heat_input_scale must be numeric") from exc
    if scale <= 0:
        raise TaskConfigError("heat_input_scale must be positive")
    validated["heat_input_scale"] = scale

    return validated


def safety_flags(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "allow_cae_export": bool(config.get("allow_cae_export", False)),
        "allow_odb_read": bool(config.get("allow_odb_read", False)),
        "odb_read_mode": config.get("odb_read_mode", "disabled"),
        "allow_solver_submit": bool(config.get("allow_solver_submit", False)),
        "allow_abqjobpilot": bool(config.get("allow_abqjobpilot", False)),
        "allow_abqjobpilot_preflight": bool(config.get("allow_abqjobpilot_preflight", False)),
        "allow_abqjobpilot_dry_run_enqueue": bool(config.get("allow_abqjobpilot_dry_run_enqueue", False)),
        "allow_jobpilot_enqueue_authorization": bool(config.get("allow_jobpilot_enqueue_authorization", False)),
        "allow_abqjobpilot_real_enqueue": bool(config.get("allow_abqjobpilot_real_enqueue", False)),
        "allow_abqjobpilot_status_poll": bool(config.get("allow_abqjobpilot_status_poll", False)),
        "allow_llm": bool(config.get("allow_llm", False)),
        "allow_cae_modify": bool(config.get("allow_cae_modify", False)),
    }


def _require_bool(config: dict[str, Any], key: str) -> None:
    if key not in config:
        raise TaskConfigError(f"missing required safety field: {key}")
    if not isinstance(config[key], bool):
        raise TaskConfigError(f"{key} must be boolean")
