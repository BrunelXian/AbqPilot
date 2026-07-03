from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file
from abqpilot.patching.real_sanity_base_candidate import CANDIDATE_HEAT_LINE, SOURCE_HEAT_LINE
from abqpilot.solver.solver_artifacts import read_json


MIN_REAL_INP_BYTES = 100_000
SAFE_JOB_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{0,79}$")


def validate_solver_candidate(
    candidate_inp: str | Path,
    source_inp: str | Path,
    evidence_dir: str | Path,
    solver_run_dir: str | Path,
    job_name: str,
    cpus: int,
) -> dict[str, Any]:
    candidate = Path(candidate_inp)
    source = Path(source_inp)
    evidence = Path(evidence_dir)
    run_dir = Path(solver_run_dir)
    summary = read_json(evidence / "real_sanity_base_patch_candidate_summary.json")
    diff = read_json(evidence / "patch_diff_report.json")
    static = read_json(evidence / "static_validation_report.json")
    physics = read_json(evidence / "physics_guard_report.json")

    fixture_only = _fixture_only(candidate, summary)
    checks = {
        "candidate_exists": candidate.exists(),
        "traceable_to_sanity_base": summary.get("real_sanity_base_source_used") is True
        or summary.get("candidate_traceability") == "sanity-base-derived",
        "not_fixture_only": not fixture_only,
        "candidate_size_realistic": candidate.exists() and candidate.stat().st_size >= MIN_REAL_INP_BYTES,
        "source_exists": source.exists(),
        "source_sha256_recorded": bool(summary.get("source_inp_sha256") or summary.get("source_original_sha256")),
        "candidate_sha256_recorded": bool(summary.get("candidate_inp_sha256")),
        "candidate_sha256_matches": candidate.exists() and summary.get("candidate_inp_sha256") == sha256_file(candidate),
        "source_sha256_matches": source.exists()
        and (summary.get("source_inp_sha256") == sha256_file(source) or summary.get("source_original_sha256") == sha256_file(source)),
        "patch_operation_recorded": bool(summary.get("exact_heat_flux_change")),
        "changed_lines_known": summary.get("changed_lines_count") is not None,
        "unrelated_changes_zero": summary.get("unrelated_changes_count") == 0,
        "static_validator_pass": summary.get("static_validator_status") == "PASS" or static.get("passed") is True,
        "diff_guard_pass": summary.get("diff_guard_status") == "PASS" or diff.get("allowed") is True,
        "physics_guard_pass": summary.get("physics_guard_status") == "PASS" or physics.get("passed") is True,
        "no_planned_lck": not (run_dir / f"{job_name}.lck").exists(),
        "job_name_safe": bool(SAFE_JOB_RE.match(job_name)),
        "cpus_valid": isinstance(cpus, int) and 1 <= cpus <= 14,
        "candidate_heat_flux_2x": candidate.exists() and CANDIDATE_HEAT_LINE in candidate.read_text(encoding="utf-8", errors="replace"),
        "source_heat_flux_1x": source.exists() and SOURCE_HEAT_LINE in source.read_text(encoding="utf-8", errors="replace"),
    }
    errors = [name for name, ok in checks.items() if not ok]
    verdict = (
        "WARNING_ABQPILOT_SIMULATION_SOURCE_NOT_SANITY_BASE_DERIVED"
        if fixture_only or not checks["traceable_to_sanity_base"]
        else "SOLVER_CANDIDATE_ELIGIBLE"
        if not errors
        else "SOLVER_AUTOMATION_BLOCKED_INVALID_CANDIDATE"
    )
    return {
        "verdict": verdict,
        "eligible": verdict == "SOLVER_CANDIDATE_ELIGIBLE",
        "fixture_only": fixture_only,
        "checks": checks,
        "errors": errors,
        "candidate_inp_path": str(candidate),
        "source_inp_path": str(source),
        "candidate_inp_sha256": sha256_file(candidate) if candidate.exists() else None,
        "source_inp_sha256": sha256_file(source) if source.exists() else None,
        "changed_lines_count": summary.get("changed_lines_count"),
        "unrelated_changes_count": summary.get("unrelated_changes_count"),
        "static_validator_status": "PASS" if checks["static_validator_pass"] else "FAIL",
        "diff_guard_status": "PASS" if checks["diff_guard_pass"] else "FAIL",
        "physics_guard_status": "PASS" if checks["physics_guard_pass"] else "FAIL",
        "exact_patch_operation": summary.get("exact_heat_flux_change"),
    }


def _fixture_only(candidate: Path, summary: dict[str, Any]) -> bool:
    if summary.get("fixture_reclassified_as_workflow_only") and not summary.get("real_sanity_base_source_used"):
        return True
    if candidate.exists() and candidate.stat().st_size < MIN_REAL_INP_BYTES:
        return True
    if candidate.exists() and "STEEL_FIXTURE" in candidate.read_text(encoding="utf-8", errors="replace"):
        return True
    return False
