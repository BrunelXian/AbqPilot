from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.patching.dflux_lifecycle_patch import (
    preview_dflux_deactivation_patch,
    validate_dflux_lifecycle,
)
from abqpilot.patching.dflux_lifecycle_report import (
    render_dflux_lifecycle_summary,
    render_successful_comparison_markdown,
)
from abqpilot.patching.dflux_lifecycle_schema import INSERTED_KEYWORD, build_patch_plan, validate_patch_plan
from abqpilot.tools.physics_guard_tool import PhysicsGuard
from abqpilot.tools.static_validator_tool import StaticValidator


DEFAULT_OUTPUT_DIR = Path("D:/Projects/AbqPilot-v2/runs/stage4_3_guarded_dflux_deactivation_patch_preview")


def preview_dflux_deactivation_patch_stage(
    source_inp: str | Path,
    output_dir: str | Path | None = None,
    scan_step: str = "step_scan_00",
    cooling_step: str = "Step_cool_00",
    load_name: str = "load_body_hflux_00",
    compare_successful_job_dir: str | Path | None = None,
) -> dict[str, Any]:
    source = Path(source_inp)
    out = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    preview = out / f"{source.stem}_dflux_deactivated_preview.inp"
    context = {
        "schema_version": "0.1",
        "stage": "Stage 4.3",
        "source_inp": str(source),
        "output_dir": str(out),
        "scan_step": scan_step,
        "cooling_step": cooling_step,
        "load_name": load_name,
        "solver_run": False,
        "odb_opened": False,
    }
    plan = build_patch_plan(str(source), str(preview), scan_step, cooling_step, load_name)
    plan_validation = validate_patch_plan(plan)
    application = preview_dflux_deactivation_patch(source, preview, scan_step, cooling_step)
    if not application.get("allowed"):
        validation = _blocked_validation(application)
        summary = _summary(plan, application, validation, "DFLUX_DEACTIVATION_PATCH_PREVIEW_BLOCKED")
        paths = _write_artifacts(out, context, plan, application, validation, summary, compare_successful_job_dir, source)
        return _result(summary, paths, success=False)

    static_report = StaticValidator().validate(
        preview,
        target_region=None,
        required_tokens=["*Heading", "*Step", "*End Step", "*Output", "NT"],
    )
    lifecycle_validation = validate_dflux_lifecycle(source, preview, scan_step, cooling_step)
    diff_report = lifecycle_validation["diff_report"]
    physics_report = PhysicsGuard().check(diff_report)
    validation = {
        "schema_version": "0.1",
        "stage": "Stage 4.3",
        "patch_plan_validation": plan_validation,
        "static_validator": _status(static_report, "passed"),
        "diff_guard": _status(diff_report, "allowed"),
        "physics_guard": _status(physics_report, "passed"),
        "dflux_lifecycle_validator": _status(lifecycle_validation, "passed"),
        "source_inp_unchanged": application.get("source_inp_unchanged") is True,
        "preview_inp_created": preview.exists(),
        "cooling_step_has_dflux_op_new": lifecycle_validation.get("cooling_step_has_dflux_op_new"),
        "cooling_step_positive_bf_lines": lifecycle_validation.get("cooling_step_positive_bf_lines"),
        "scan_step_bf_preserved": lifecycle_validation.get("scan_step_bf_preserved"),
        "unrelated_changes_count": diff_report.get("unrelated_changes_count"),
        "solver_run": False,
        "odb_opened": False,
        "static_validation_report": static_report,
        "diff_report": diff_report,
        "physics_guard_report": physics_report,
        "dflux_lifecycle_report": lifecycle_validation,
    }
    ready = all(
        [
            validation["static_validator"] == "PASS",
            validation["diff_guard"] == "PASS",
            validation["physics_guard"] == "PASS",
            validation["dflux_lifecycle_validator"] == "PASS",
            validation["source_inp_unchanged"],
            validation["preview_inp_created"],
            validation["cooling_step_has_dflux_op_new"],
            validation["cooling_step_positive_bf_lines"] == 0,
            validation["scan_step_bf_preserved"],
            validation["unrelated_changes_count"] == 0,
        ]
    )
    verdict = "DFLUX_DEACTIVATION_PATCH_PREVIEW_READY" if ready else "DFLUX_DEACTIVATION_PATCH_PREVIEW_FAILED_VALIDATION"
    summary = _summary(plan, application, validation, verdict)
    paths = _write_artifacts(out, context, plan, application, validation, summary, compare_successful_job_dir, source)
    return _result(summary, paths, success=ready)


def compare_successful_failed_2x(successful_job_dir: str | Path | None, failed_source_inp: Path) -> dict[str, Any]:
    if successful_job_dir is None:
        return {
            "successful_2x_job_file_comparison_available": False,
            "files": {},
            "findings": ["No successful job directory supplied."],
        }
    root = Path(successful_job_dir)
    files = {suffix: root / f"sanity_base_power_2x{suffix}" for suffix in [".inp", ".log", ".sta", ".msg", ".dat"]}
    existing = {key.lstrip("."): str(path) for key, path in files.items() if path.exists()}
    findings: list[str] = []
    if not existing:
        return {
            "successful_2x_job_file_comparison_available": False,
            "files": {},
            "findings": ["No successful 2x job text files found."],
        }
    if files[".inp"].exists():
        text = files[".inp"].read_text(encoding="utf-8", errors="replace")
        findings.append(f"successful INP contains DFLUX OP=NEW: {'*Dflux, OP=NEW'.lower() in text.lower()}")
        findings.append(f"successful INP contains Step_cool_00: {'Step_cool_00' in text}")
    else:
        findings.append("successful 2x INP not found; compared available logs only.")
    for suffix in [".sta", ".log", ".dat", ".msg"]:
        path = files[suffix]
        if path.exists():
            body = path.read_text(encoding="utf-8", errors="replace")
            findings.append(f"{path.name} completion evidence: {'COMPLETED' in body.upper()}")
    findings.append(f"failed source inspected: {failed_source_inp}")
    return {
        "successful_2x_job_file_comparison_available": True,
        "files": existing,
        "findings": findings,
    }


def _blocked_validation(application: dict[str, Any]) -> dict[str, Any]:
    return {
        "static_validator": "SKIPPED",
        "diff_guard": "SKIPPED",
        "physics_guard": "SKIPPED",
        "dflux_lifecycle_validator": "FAIL",
        "source_inp_unchanged": application.get("source_inp_unchanged") is True,
        "preview_inp_created": False,
        "cooling_step_has_dflux_op_new": False,
        "cooling_step_positive_bf_lines": None,
        "scan_step_bf_preserved": False,
        "unrelated_changes_count": None,
        "solver_run": False,
        "odb_opened": False,
        "errors": application.get("errors", []),
    }


def _summary(plan: dict[str, Any], application: dict[str, Any], validation: dict[str, Any], verdict: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 4.3",
        "verdict": verdict,
        "patch_type": "dflux_deactivation_reset",
        "mcp_guard_subcheck": "MCPGuard.load_lifecycle.body_heat_flux_dflux_bf",
        "source_inp": plan.get("source_inp"),
        "candidate_preview_inp": plan.get("candidate_preview_inp"),
        "scan_step": plan.get("scan_step"),
        "cooling_step": plan.get("cooling_step"),
        "load_name": plan.get("load_name"),
        "inserted_keyword": INSERTED_KEYWORD,
        "insertion_line": application.get("insertion_line"),
        "inserted_lines": application.get("inserted_lines", []),
        "inserted_lines_count": application.get("inserted_lines_count", 0),
        "static_validator": validation.get("static_validator"),
        "diff_guard": validation.get("diff_guard"),
        "physics_guard": validation.get("physics_guard"),
        "dflux_lifecycle_validator": validation.get("dflux_lifecycle_validator"),
        "source_inp_unchanged": validation.get("source_inp_unchanged"),
        "preview_inp_created": validation.get("preview_inp_created"),
        "cooling_step_has_dflux_op_new": validation.get("cooling_step_has_dflux_op_new"),
        "cooling_step_positive_bf_lines": validation.get("cooling_step_positive_bf_lines"),
        "scan_step_bf_preserved": validation.get("scan_step_bf_preserved"),
        "unrelated_changes_count": validation.get("unrelated_changes_count"),
        "run_solver_now": False,
        "solver_run": False,
        "odb_opened": False,
        "requires_human_review": True,
        "next_allowed_action": "Human review the preview INP before any future controlled solver attempt.",
    }


def _write_artifacts(
    out: Path,
    context: dict[str, Any],
    plan: dict[str, Any],
    application: dict[str, Any],
    validation: dict[str, Any],
    summary: dict[str, Any],
    compare_successful_job_dir: str | Path | None,
    source: Path,
) -> dict[str, str]:
    comparison = compare_successful_failed_2x(compare_successful_job_dir, source)
    payloads: dict[str, Any] = {
        "dflux_lifecycle_patch_context.json": context,
        "dflux_lifecycle_patch_plan.json": plan,
        "dflux_lifecycle_diff_report.json": validation.get("diff_report") or application,
        "dflux_lifecycle_validation.json": validation,
        "dflux_lifecycle_preview_summary.md": render_dflux_lifecycle_summary(summary),
        "successful_vs_failed_2x_comparison.json": comparison,
        "successful_vs_failed_2x_comparison.md": render_successful_comparison_markdown(comparison),
    }
    paths: dict[str, str] = {}
    for name, payload in payloads.items():
        path = out / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        paths[Path(name).stem] = str(path)
    candidate = Path(plan["candidate_preview_inp"])
    if candidate.exists():
        paths["candidate_preview_inp"] = str(candidate)
    paths["artifact_dir"] = str(out)
    return paths


def _result(summary: dict[str, Any], paths: dict[str, str], success: bool) -> dict[str, Any]:
    return {
        "command": "preview-dflux-deactivation-patch",
        "verdict": summary["verdict"],
        "success": success,
        "details": summary,
        "output_paths": paths,
        "warnings": [],
        "errors": [] if success else ["DFLUX lifecycle patch preview did not pass validation."],
    }


def _status(report: dict[str, Any], field: str) -> str:
    return "PASS" if report.get(field) else "FAIL"
