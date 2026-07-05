from __future__ import annotations

from typing import Any


UNSAFE_PREVIEW_CLAIM_KEYS = {
    "final_evidence_approved",
    "final_verdict_frozen",
    "solver_approved",
    "odb_metrics_approved",
    "task_final_evidence_ledger_updated",
    "codex_summary_is_final_evidence",
    "automatic_execution_performed",
    "solver_run",
    "queue_runner_launched",
    "odb_opened",
    "codex_cli_called",
    "shell_true_used",
}


SAFETY_FIELD_KEYS = UNSAFE_PREVIEW_CLAIM_KEYS | {
    "solver_started",
    "abqjobpilot_gui_launched",
    "source_sanity_base_mutated",
    "generic_" + "sub" + "process_added",
    "env_read",
    "forbidden_path_touched",
}


def collect_safety_fields(payload: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    _collect_fields(payload, fields)
    return fields


def find_unsafe_claims(payload: Any, *, path: str | None = None) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    _find_claims(payload, claims, path=path, prefix="")
    return claims


def has_unsafe_claims(payload: Any) -> bool:
    return bool(find_unsafe_claims(payload))


def _collect_fields(payload: Any, fields: dict[str, Any], prefix: str = "") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            if key in SAFETY_FIELD_KEYS or key == "safety_flags" or key == "forbidden_actions":
                fields[full_key] = value
            if isinstance(value, (dict, list)):
                _collect_fields(value, fields, full_key)
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            _collect_fields(item, fields, f"{prefix}[{index}]")


def _find_claims(payload: Any, claims: list[dict[str, Any]], *, path: str | None, prefix: str) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            if key in UNSAFE_PREVIEW_CLAIM_KEYS and value is True:
                claims.append({"path": path, "key": full_key, "value": True})
            if isinstance(value, (dict, list)):
                _find_claims(value, claims, path=path, prefix=full_key)
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            _find_claims(item, claims, path=path, prefix=f"{prefix}[{index}]")
