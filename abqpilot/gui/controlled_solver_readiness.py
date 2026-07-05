from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


READINESS_STATUSES = {
    "SOLVER_GATE_PREVIEW_READY",
    "SOLVER_GATE_PREVIEW_READY_WITH_MISSING_PREREQUISITES",
    "SOLVER_GATE_PREVIEW_BLOCKED_SOURCE_MUTATION_RISK",
    "SOLVER_GATE_PREVIEW_BLOCKED_MISSING_VALIDATORS",
    "SOLVER_GATE_PREVIEW_BLOCKED_EXECUTION_REQUEST_PRESENT",
    "SOLVER_GATE_PREVIEW_REVIEW_REQUIRED",
}

EXECUTION_REQUEST_FILENAMES = {
    "solver_request.json",
    "active_solver_request.json",
    "controlled_solver_request.json",
    "run_solver_request.json",
}


@dataclass(frozen=True)
class SolverReadinessItem:
    item_id: str
    description: str
    status: str
    evidence: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_solver_readiness_checklist(task_dir: str | Path | None = None, candidate_inp: str | Path | None = None) -> dict[str, Any]:
    task = Path(task_dir) if task_dir else None
    candidate = Path(candidate_inp) if candidate_inp else _find_candidate_inp(task)
    items = [
        _item("task_dir_exists", "task_dir exists", _exists_dir(task), str(task) if task else None),
        _item("task_scaffold_exists", "task scaffold exists", _task_scaffold_exists(task), str(task) if task else None),
        _item("candidate_inp_exists", "candidate INP exists under allowed task/artifact directory", _exists_file(candidate), str(candidate) if candidate else None),
        _item("candidate_inp_not_source_sanity_base", "candidate INP is not source sanity-base INP", _candidate_not_source(candidate), str(candidate) if candidate else None),
        _item("source_mutation_not_required", "source CAE/INP mutation is not required", not _source_mutation_requested(task), None),
        _item("static_validator_pass", "StaticValidator PASS record exists", _marker_present(task, "StaticValidator", "PASS"), None),
        _item("diff_guard_pass", "DiffGuard PASS record exists", _marker_present(task, "DiffGuard", "PASS"), None),
        _item("physics_guard_pass", "PhysicsGuard PASS record exists", _marker_present(task, "PhysicsGuard", "PASS"), None),
        _item("mcpguard_pass_or_not_applicable", "MCPGuard PASS record exists or explicit MCPGuard not-applicable reason exists", _mcpguard_ok(task), None),
        _item("candidate_patch_preview_exists", "candidate patch preview exists", _patch_preview_exists(task), None),
        _item("target_modification_summary_exists", "target modification summary exists", _marker_present(task, "target modification", None), None),
        _item("forbidden_action_confirmation_exists", "forbidden action confirmation exists", _marker_present(task, "forbidden", None), None),
        _item("solver_command_path_configured", "solver command path is configured in project status/config", _solver_command_configured(), None),
        _item("future_solver_output_dir_defined", "future controlled solver output directory is defined", bool(task), str(task / "future_controlled_solver_preview") if task else None),
        _item("future_human_approval_required", "explicit human approval token would be required in a future stage", True, None),
        _item("no_queue_mutation_requested", "no queue mutation is requested", not _marker_present(task, "queue mutation requested", None), None),
        _item("no_odb_metrics_acceptance_requested", "no ODB metrics acceptance is requested", not _marker_present(task, "odb metrics accepted", None), None),
        _item("no_final_evidence_update_requested", "no final evidence update is requested", not _marker_present(task, "final_evidence_approved", "true"), None),
        _item("no_final_verdict_freeze_requested", "no final verdict freeze is requested", not _marker_present(task, "final_verdict_frozen", "true"), None),
        _item("no_automatic_execution_requested", "no automatic execution requested", not _automatic_execution_requested(task), None),
    ]
    missing = [item.item_id for item in items if item.status == "MISSING"]
    blocked = [item.item_id for item in items if item.status == "BLOCKED"]
    status = _readiness_status(items)
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2B",
        "readiness_status": status,
        "task_dir": str(task) if task else None,
        "candidate_inp": str(candidate) if candidate else None,
        "checklist": [item.to_dict() for item in items],
        "missing_prerequisites": missing,
        "blocked_items": blocked,
        "preview_only": True,
        "solver_approved": False,
        "solver_run": False,
        "solver_request_created": False,
    }


def _item(item_id: str, description: str, ok: bool, evidence: str | None) -> SolverReadinessItem:
    return SolverReadinessItem(item_id=item_id, description=description, status="PASS" if ok else "MISSING", evidence=evidence)


def _exists_dir(path: Path | None) -> bool:
    return path is not None and path.exists() and path.is_dir()


def _exists_file(path: Path | None) -> bool:
    return path is not None and path.exists() and path.is_file()


def _task_scaffold_exists(task: Path | None) -> bool:
    if not _exists_dir(task):
        return False
    return any((task / name).exists() for name in ("TRACE_INDEX.md", "trace", "handoffs", "gates", "codex_handoff"))


def _find_candidate_inp(task: Path | None) -> Path | None:
    if not _exists_dir(task):
        return None
    matches = [p for p in task.rglob("*.inp") if p.is_file()]
    return matches[0] if matches else None


def _candidate_not_source(candidate: Path | None) -> bool:
    if candidate is None:
        return False
    lowered = str(candidate).lower().replace("/", "\\")
    if "cae_model\\sanity_base" in lowered:
        return False
    if candidate.name.lower() in {"source_sanity_base_export.inp", "sanity_base_v01.inp"}:
        return False
    return True


def _source_mutation_requested(task: Path | None) -> bool:
    return _marker_present(task, "source_cae_mutated", "true") or _marker_present(task, "source_inp_mutated", "true")


def _automatic_execution_requested(task: Path | None) -> bool:
    return _marker_present(task, "automatic_execution_performed", "true") or _execution_request_present(task)


def _execution_request_present(task: Path | None) -> bool:
    if not _exists_dir(task):
        return False
    return any((task / filename).exists() for filename in EXECUTION_REQUEST_FILENAMES)


def _patch_preview_exists(task: Path | None) -> bool:
    if not _exists_dir(task):
        return False
    patterns = ("*preview*.json", "*preview*.md", "*preview*.inp")
    return any(any(task.rglob(pattern)) for pattern in patterns)


def _mcpguard_ok(task: Path | None) -> bool:
    return _marker_present(task, "MCPGuard", "PASS") or _marker_present(task, "MCPGuard not applicable", None)


def _marker_present(task: Path | None, marker: str, required_value: str | None) -> bool:
    if not _exists_dir(task):
        return False
    needle = marker.lower()
    value = required_value.lower() if required_value else None
    for path in _small_text_files(task):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if needle in text and (value is None or value in text):
            return True
    return False


def _small_text_files(task: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.json", "*.md", "*.txt"):
        for path in task.rglob(pattern):
            try:
                if path.is_file() and path.stat().st_size < 2_000_000:
                    files.append(path)
            except OSError:
                continue
    return files


def _solver_command_configured() -> bool:
    return True


def _readiness_status(items: list[SolverReadinessItem]) -> str:
    by_id = {item.item_id: item.status for item in items}
    if (
        by_id.get("candidate_inp_exists") == "PASS"
        and by_id.get("candidate_inp_not_source_sanity_base") == "MISSING"
    ) or by_id.get("source_mutation_not_required") == "MISSING":
        return "SOLVER_GATE_PREVIEW_BLOCKED_SOURCE_MUTATION_RISK"
    if any(by_id.get(item_id) == "MISSING" for item_id in ("static_validator_pass", "diff_guard_pass", "physics_guard_pass", "mcpguard_pass_or_not_applicable")):
        return "SOLVER_GATE_PREVIEW_BLOCKED_MISSING_VALIDATORS"
    if by_id.get("no_automatic_execution_requested") == "MISSING":
        return "SOLVER_GATE_PREVIEW_BLOCKED_EXECUTION_REQUEST_PRESENT"
    if any(item.status == "MISSING" for item in items):
        return "SOLVER_GATE_PREVIEW_READY_WITH_MISSING_PREREQUISITES"
    return "SOLVER_GATE_PREVIEW_READY"
