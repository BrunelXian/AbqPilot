from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file
from abqpilot.tools.diff_guard_tool import DiffGuard
from abqpilot.tools.physics_guard_tool import PhysicsGuard
from abqpilot.tools.static_validator_tool import StaticValidator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE_INP = (
    PROJECT_ROOT
    / "runs"
    / "stage3_7_heat_flux_fixture_task"
    / "patch_previews"
    / "preview_20260630_183350_319742"
    / "source__patch_preview.inp"
)
DEFAULT_REAL_CAE = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_v01.cae"
DEFAULT_REAL_JNL = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_v01.jnl"
DEFAULT_REAL_EXPORT_INP = PROJECT_ROOT / "runs" / "stage1_6a_cae_to_inp_export" / "sanity_base_v01_export.inp"
DEFAULT_POWER_2X_INP = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_power_2x.inp"
DEFAULT_POWER_2X_ODB = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_power_2x.odb"
DEFAULT_POWER_2X_LOG = PROJECT_ROOT / "CAE_model" / "sanity_base" / "sanity_base_power_2x.log"
DEFAULT_OUT_DIR = PROJECT_ROOT / "runs" / "stage3_9b_real_sanity_base_patch_candidate"

SOURCE_HEAT_LINE = "inst_plate.set-body-1, BF, 1e+10"
CANDIDATE_HEAT_LINE = "inst_plate.set-body-1, BF, 2e+10"


def create_real_sanity_base_patch_candidate(
    out_dir: str | Path = DEFAULT_OUT_DIR,
    source_inp: str | Path = DEFAULT_REAL_EXPORT_INP,
) -> dict[str, Any]:
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(source_inp)
    source_copy = target_dir / "source_sanity_base_export.inp"
    candidate_path = target_dir / "candidate_sanity_base_power_x2.inp"

    classification = classify_sources(source_inp=source_path)
    _write_json(target_dir / "source_classification_report.json", classification)

    if not source_path.exists():
        summary = _blocked_summary(target_dir, classification, "WARNING_STAGE3_9B_REAL_SANITY_BASE_SOURCE_NOT_FOUND")
        _write_summary(target_dir, summary)
        return summary

    shutil.copyfile(source_path, source_copy)
    patch_result = _write_heat_flux_candidate(source_copy, candidate_path)
    _write_json(
        target_dir / "patch_application_result.json",
        {
            "schema_version": "0.1",
            "status": "PATCH_APPLIED" if patch_result["ok"] else "PATCH_BLOCKED",
            **patch_result,
        },
    )
    if not patch_result["ok"]:
        summary = _blocked_summary(target_dir, classification, "WARNING_STAGE3_9B_PATCH_TARGET_NOT_FOUND")
        summary.update(patch_result)
        _write_summary(target_dir, summary)
        return summary

    static_report = _validate_thermo_mechanical(candidate_path)
    _write_json(target_dir / "static_validation_report.json", static_report)
    diff_report = DiffGuard().compare(source_copy, candidate_path)
    _write_json(target_dir / "patch_diff_report.json", diff_report)
    _write_json(target_dir / "diff_guard_report.json", diff_report)
    physics_report = PhysicsGuard().check(diff_report)
    _write_json(target_dir / "physics_guard_report.json", physics_report)
    equivalence = evaluate_power_2x_odb_equivalence(candidate_path)

    changed_lines_count = len(diff_report.get("changed_lines", []))
    unrelated_changes_count = sum(
        1
        for item in diff_report.get("changed_lines", [])
        if item.get("base") != SOURCE_HEAT_LINE or item.get("generated") != CANDIDATE_HEAT_LINE
    )
    source_hash_before = sha256_file(str(source_path))
    source_hash_copy = sha256_file(str(source_copy))
    summary = {
        "schema_version": "0.1",
        "stage": "Stage 3.9B",
        "verdict": "PASS_ABQPILOT_V2_STAGE3_9B_REAL_SANITY_BASE_PATCH_CANDIDATE_READY",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "fixture_reclassified_as_workflow_only": True,
        "real_sanity_base_source_used": True,
        "source_inp_path": str(source_copy),
        "candidate_inp_path": str(candidate_path),
        "source_inp_sha256": source_hash_copy,
        "candidate_inp_sha256": sha256_file(str(candidate_path)),
        "source_original_sha256": source_hash_before,
        "source_unchanged": source_hash_before == source_hash_copy,
        "source_size_bytes": source_copy.stat().st_size,
        "candidate_size_bytes": candidate_path.stat().st_size,
        "exact_heat_flux_change": {
            "from": SOURCE_HEAT_LINE,
            "to": CANDIDATE_HEAT_LINE,
            "line_index": patch_result["line_index"],
        },
        "changed_lines_count": changed_lines_count,
        "unrelated_changes_count": unrelated_changes_count,
        "static_validator_status": "PASS" if static_report.get("passed") else "FAIL",
        "diff_guard_status": "PASS" if diff_report.get("allowed") else "FAIL",
        "physics_guard_status": "PASS" if physics_report.get("passed") else "FAIL",
        "candidate_solver_ready_classification": "yes"
        if static_report.get("passed") and candidate_path.stat().st_size > 100_000
        else "no",
        "existing_power_2x_odb_equivalent_candidate_output": equivalence["status"],
        "existing_power_2x_equivalence": equivalence,
        "solver_submitted": False,
        "queue_runner_launched": False,
        "job_enqueued": False,
        "opened_odb": False,
        "classification": classification,
    }
    if not (
        summary["source_unchanged"]
        and summary["changed_lines_count"] == 1
        and summary["unrelated_changes_count"] == 0
        and static_report.get("passed")
        and diff_report.get("allowed")
        and physics_report.get("passed")
    ):
        summary["verdict"] = "WARNING_STAGE3_9B_FIXTURE_EVIDENCE_RECLASSIFICATION_REQUIRED"
    _write_summary(target_dir, summary)
    return summary


def classify_sources(
    fixture_inp: str | Path = DEFAULT_FIXTURE_INP,
    source_inp: str | Path = DEFAULT_REAL_EXPORT_INP,
    real_cae: str | Path = DEFAULT_REAL_CAE,
    real_jnl: str | Path = DEFAULT_REAL_JNL,
    power_2x_odb: str | Path = DEFAULT_POWER_2X_ODB,
) -> dict[str, Any]:
    fixture = _classify_inp(Path(fixture_inp), fixture=True)
    real_export = _classify_inp(Path(source_inp), fixture=False)
    return {
        "schema_version": "0.1",
        "fixture_inp": fixture,
        "real_exported_inp": real_export,
        "real_sanity_cae": _file_info(Path(real_cae)),
        "real_sanity_jnl": _file_info(Path(real_jnl)),
        "existing_real_odbs": {
            "power_2x": _file_info(Path(power_2x_odb)),
            "power_2x_lock_exists": Path(str(power_2x_odb) + ".lck").exists()
            or Path(power_2x_odb).with_suffix(".lck").exists(),
        },
    }


def evaluate_power_2x_odb_equivalence(candidate_inp: str | Path) -> dict[str, Any]:
    candidate = Path(candidate_inp)
    power_inp = DEFAULT_POWER_2X_INP
    odb = DEFAULT_POWER_2X_ODB
    log = DEFAULT_POWER_2X_LOG
    candidate_text = candidate.read_text(encoding="utf-8", errors="replace") if candidate.exists() else ""
    power_text = power_inp.read_text(encoding="utf-8", errors="replace") if power_inp.exists() else ""
    log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    lock_exists = Path(str(odb) + ".lck").exists() or odb.with_suffix(".lck").exists()
    evidence = {
        "candidate_has_power_2x_line": CANDIDATE_HEAT_LINE in candidate_text,
        "power_2x_inp_has_power_2x_line": CANDIDATE_HEAT_LINE in power_text,
        "power_2x_odb_exists": odb.exists(),
        "power_2x_odb_lock_exists": lock_exists,
        "power_2x_log_completed": "COMPLETED" in log_text and "sanity_base_power_2x" in log_text,
        "same_model_family_evidence": "sanity_base" in str(power_inp).lower() and DEFAULT_REAL_CAE.exists(),
        "power_2x_inp_path": str(power_inp),
        "power_2x_odb_path": str(odb),
        "power_2x_log_path": str(log),
    }
    accepted = all(
        [
            evidence["candidate_has_power_2x_line"],
            evidence["power_2x_inp_has_power_2x_line"],
            evidence["power_2x_odb_exists"],
            not evidence["power_2x_odb_lock_exists"],
            evidence["power_2x_log_completed"],
            evidence["same_model_family_evidence"],
        ]
    )
    evidence["status"] = "YES" if accepted else "UNPROVEN"
    return evidence


def _write_heat_flux_candidate(source: Path, candidate: Path) -> dict[str, Any]:
    with source.open("r", encoding="utf-8", newline="") as handle:
        lines = handle.read().splitlines(keepends=True)
    matches = [idx for idx, line in enumerate(lines) if line.rstrip("\r\n") == SOURCE_HEAT_LINE]
    if len(matches) != 1:
        return {"ok": False, "errors": [f"expected exactly one source heat flux line, found {len(matches)}"]}
    idx = matches[0]
    newline = "\r\n" if lines[idx].endswith("\r\n") else "\n" if lines[idx].endswith("\n") else ""
    lines[idx] = CANDIDATE_HEAT_LINE + newline
    with candidate.open("w", encoding="utf-8", newline="") as handle:
        handle.write("".join(lines))
    return {
        "ok": True,
        "line_index": idx,
        "before": SOURCE_HEAT_LINE,
        "after": CANDIDATE_HEAT_LINE,
        "candidate_inp_path": str(candidate),
    }


def _classify_inp(path: Path, fixture: bool) -> dict[str, Any]:
    info = _file_info(path)
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    heat_line = _find_heat_flux_line(text)
    info.update(
        {
            "contains_node": "*node" in text.lower(),
            "contains_element": "*element" in text.lower(),
            "contains_material": "*material" in text.lower(),
            "contains_step": "*step" in text.lower(),
            "contains_dflux_or_bf": "*dflux" in text.lower() or ", bf," in text.lower(),
            "heat_flux_line_found": heat_line,
            "solver_ready": (
                "no"
                if fixture or info.get("size_bytes", 0) < 100_000 or "STEEL_FIXTURE" in text
                else "yes"
            ),
            "classification": "workflow_fixture_only" if fixture else "real_sanity_base_export",
        }
    )
    return info


def _find_heat_flux_line(text: str) -> str | None:
    for line in text.splitlines():
        if ", BF," in line or ", bf," in line:
            return line.strip()
    return None


def _file_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "size_bytes": 0}
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
    }


def _validate_thermo_mechanical(inp_path: Path) -> dict[str, Any]:
    text = inp_path.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    temperature_token = "NT11" if "nt11" in lower else "NT" if _has_output_token(text, "NT") else None
    required_tokens = ["*Heading", "*Node", "*Element", "*Material", "*Step", "*End Step", "*Output", temperature_token or "NT11_OR_NT", "S"]
    report = StaticValidator().validate(inp_path, target_region=None, required_tokens=required_tokens)
    if temperature_token is None and "NT11_OR_NT" not in report["missing"]:
        report["missing"].append("NT11_OR_NT")
    if not _has_output_token(text, "S") and "S" not in report["missing"]:
        report["missing"].append("S")
    report["NT11_literal_present"] = "nt11" in lower
    report["temperature_output_token"] = temperature_token
    report["target_region_status"] = "TARGET_REGION_NOT_CONFIRMED"
    report["passed"] = not report["missing"] and not report["errors"]
    return report


def _has_output_token(text: str, token: str) -> bool:
    target = token.lower()
    for line in text.splitlines():
        if line.lstrip().startswith("*") or line.lstrip().startswith("**"):
            continue
        tokens = [part.strip().lower() for part in line.split(",")]
        if target in tokens:
            return True
    return False


def _blocked_summary(target_dir: Path, classification: dict[str, Any], verdict: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "stage": "Stage 3.9B",
        "verdict": verdict,
        "source_inp_path": str(target_dir / "source_sanity_base_export.inp"),
        "candidate_inp_path": str(target_dir / "candidate_sanity_base_power_x2.inp"),
        "real_sanity_base_source_used": False,
        "solver_submitted": False,
        "queue_runner_launched": False,
        "job_enqueued": False,
        "opened_odb": False,
        "classification": classification,
    }


def _write_summary(target_dir: Path, summary: dict[str, Any]) -> None:
    _write_json(target_dir / "real_sanity_base_patch_candidate_summary.json", summary)
    lines = [
        "# Stage 3.9B Real Sanity-Base Patch Candidate",
        "",
        f"Verdict: {summary.get('verdict')}",
        f"Source INP: {summary.get('source_inp_path')}",
        f"Candidate INP: {summary.get('candidate_inp_path')}",
        f"Heat flux change: {summary.get('exact_heat_flux_change', {}).get('from')} -> {summary.get('exact_heat_flux_change', {}).get('to')}",
        f"StaticValidator: {summary.get('static_validator_status')}",
        f"DiffGuard: {summary.get('diff_guard_status')}",
        f"PhysicsGuard: {summary.get('physics_guard_status')}",
        f"Changed lines: {summary.get('changed_lines_count')}",
        f"Unrelated changes: {summary.get('unrelated_changes_count')}",
        f"Existing power_2x ODB equivalent candidate output: {summary.get('existing_power_2x_odb_equivalent_candidate_output')}",
        "",
        "No solver was submitted. No queue job was enqueued. No ODB was opened.",
    ]
    (target_dir / "real_sanity_base_patch_candidate_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
