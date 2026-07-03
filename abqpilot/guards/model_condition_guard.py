from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.guards.model_condition_compare import compare_model_conditions
from abqpilot.guards.model_condition_extractor import extract_inp_conditions, extract_jnl_conditions
from abqpilot.guards.model_condition_report import render_mcp_report
from abqpilot.guards.model_condition_schema import (
    CONDITION_CATEGORIES,
    GUARD_NAME,
    GUARD_SHORT_NAME,
    MCP_BLOCKED_MISSING_CANDIDATE,
    MCP_BLOCKED_MISSING_SOURCE_INTENT,
    SCHEMA_VERSION,
    STAGE,
    validate_mcp_result,
)


DEFAULT_OUTPUT_DIR = Path("D:/Projects/AbqPilot-v2/runs/stage4_5_model_condition_preservation_guard")


def run_model_condition_guard(
    source_jnl: str | Path,
    source_inp: str | Path,
    candidate_inp: str | Path,
    solver_inp: str | Path | None = None,
    output_dir: str | Path | None = None,
    declared_target_changes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    source_jnl_path = Path(source_jnl)
    source_inp_path = Path(source_inp)
    candidate_path = Path(candidate_inp)
    solver_path = Path(solver_inp) if solver_inp else None
    if not source_jnl_path.exists():
        return _blocked(out, MCP_BLOCKED_MISSING_SOURCE_INTENT, source_jnl_path, source_inp_path, candidate_path, solver_path, "source JNL is missing")
    if not candidate_path.exists():
        return _blocked(out, MCP_BLOCKED_MISSING_CANDIDATE, source_jnl_path, source_inp_path, candidate_path, solver_path, "candidate INP is missing")

    source_intent = extract_jnl_conditions(source_jnl_path)
    source_exported = extract_inp_conditions(source_inp_path)
    candidate = extract_inp_conditions(candidate_path)
    solver = extract_inp_conditions(solver_path) if solver_path and solver_path.exists() else None
    comparison = compare_model_conditions(source_intent, source_exported, candidate, solver, declared_target_changes or [])
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "guard_name": GUARD_NAME,
        "guard_short_name": GUARD_SHORT_NAME,
        "source_intent_path": str(source_jnl_path),
        "source_exported_inp": str(source_inp_path),
        "candidate_inp": str(candidate_path),
        "solver_inp": str(solver_path) if solver_path else None,
        "declared_target_changes": declared_target_changes or [],
        "condition_categories_checked": CONDITION_CATEGORIES,
        "source_condition_intent": source_intent,
        "source_exported_condition_representation": source_exported,
        "candidate_condition_representation": candidate,
        "solver_condition_representation": solver or {},
        "condition_findings": comparison["condition_findings"],
        "target_patch_isolation": comparison["target_patch_isolation"],
        "guard_status": comparison["guard_status"],
        "eligible_for_solver": comparison["eligible_for_solver"],
        "requires_human_review": True,
        "safety_flags": {"solver_run": False, "odb_opened": False, "queue_runner_launched": False, "llm_used": False},
    }
    result["schema_validation"] = validate_mcp_result(result)
    paths = _write_artifacts(out, source_intent, source_exported, candidate, solver or {}, result)
    return {
        "command": "run-model-condition-guard",
        "verdict": "MCP_GUARD_PASS" if result["guard_status"] == "MCP_PASS" else "MCP_GUARD_FAIL_CONDITION_LOSS" if result["guard_status"] == "MCP_FAIL_CONDITION_LOSS" else result["guard_status"],
        "success": result["guard_status"] == "MCP_PASS",
        "details": result,
        "output_paths": paths,
        "errors": [] if result["guard_status"] == "MCP_PASS" else [result["guard_status"]],
        "warnings": [],
    }


def _blocked(out: Path, status: str, source_jnl: Path, source_inp: Path, candidate: Path, solver: Path | None, error: str) -> dict[str, Any]:
    result = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "guard_name": GUARD_NAME,
        "guard_short_name": GUARD_SHORT_NAME,
        "source_intent_path": str(source_jnl),
        "source_exported_inp": str(source_inp),
        "candidate_inp": str(candidate),
        "solver_inp": str(solver) if solver else None,
        "declared_target_changes": [],
        "condition_categories_checked": [],
        "source_condition_intent": {},
        "candidate_condition_representation": {},
        "solver_condition_representation": {},
        "condition_findings": [],
        "target_patch_isolation": {"status": "REVIEW", "authorized_changes": [], "unauthorized_changes": []},
        "guard_status": status,
        "eligible_for_solver": False,
        "requires_human_review": True,
        "errors": [error],
    }
    paths = _write_artifacts(out, {}, {}, {}, {}, result)
    return {"command": "run-model-condition-guard", "verdict": status, "success": False, "details": result, "output_paths": paths, "errors": [error], "warnings": []}


def _write_artifacts(
    out: Path,
    source_intent: dict[str, Any],
    source_exported: dict[str, Any],
    candidate: dict[str, Any],
    solver: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, str]:
    payloads: dict[str, Any] = {
        "model_condition_source_intent.json": source_intent,
        "model_condition_source_exported_inp.json": source_exported,
        "model_condition_candidate_inp.json": candidate,
        "model_condition_solver_inp.json": solver,
        "model_condition_preservation_result.json": result,
        "model_condition_preservation_report.md": render_mcp_report(result),
    }
    paths: dict[str, str] = {}
    for name, payload in payloads.items():
        path = out / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        paths[Path(name).stem] = str(path)
    paths["artifact_dir"] = str(out)
    return paths
