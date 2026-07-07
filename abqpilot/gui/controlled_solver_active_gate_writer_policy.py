from __future__ import annotations

from pathlib import Path
from typing import Any


FORBIDDEN_ROOT = Path(r"D:\Users\wuxia\Documents\AbqPilot")
PROJECT_ROOT = Path(r"D:\Projects\AbqPilot-v2")


def evaluate_active_gate_writer_target(
    target_dir: str | Path,
    fixture_mode: bool,
    stage5_2f_smoke_mode: bool = False,
    project_root: str | Path = PROJECT_ROOT,
    forbidden_root: str | Path = FORBIDDEN_ROOT,
) -> dict[str, Any]:
    target = Path(target_dir)
    root = Path(project_root)
    forbidden = Path(forbidden_root)
    target_abs = _absolute(target)
    root_abs = _absolute(root)
    forbidden_abs = _absolute(forbidden)
    if not fixture_mode and not stage5_2f_smoke_mode:
        return _result("ACTIVE_GATE_WRITER_DISABLED_FOR_REAL_TASKS", target_abs)
    if _is_relative_to(target_abs, forbidden_abs):
        return _result("ACTIVE_GATE_WRITER_BLOCKED_FORBIDDEN_ROOT", target_abs, forbidden_root=True)
    if _is_queue_runtime_status_path(target_abs):
        return _result("ACTIVE_GATE_WRITER_BLOCKED_QUEUE_RUNTIME_STATUS_PATH", target_abs, queue_runtime_status_path=True)
    if _is_source_sanity_base_path(target_abs):
        return _result("ACTIVE_GATE_WRITER_BLOCKED_SOURCE_MODEL_PATH", target_abs, source_sanity_base_path=True)
    if stage5_2f_smoke_mode:
        if _is_stage5_2f_smoke_gate_path(target_abs, root_abs):
            return _result("ACTIVE_GATE_WRITER_STAGE5_2F_SMOKE_TARGET_ALLOWED", target_abs, allowed=True, smoke_task_only=True)
        if _is_relative_to(target_abs, root_abs / "runs" / "tasks"):
            return _result("ACTIVE_GATE_WRITER_BLOCKED_REAL_ARBITRARY_TASK", target_abs, real_arbitrary_task=True)
        return _result("ACTIVE_GATE_WRITER_BLOCKED_UNSUPPORTED_STAGE", target_abs)
    if _is_real_task_gate_path(target_abs, root_abs):
        return _result("ACTIVE_GATE_WRITER_BLOCKED_REAL_TASK_GATE_PATH", target_abs, real_task_gate_path=True)
    if not _is_fixture_path(target_abs, root_abs):
        return _result("ACTIVE_GATE_WRITER_BLOCKED_NON_FIXTURE_PATH", target_abs)
    return _result("ACTIVE_GATE_WRITER_TARGET_ALLOWED", target_abs, allowed=True)


def _is_fixture_path(target: Path, project_root: Path) -> bool:
    parts = {part.lower() for part in target.parts}
    if _is_relative_to(target, project_root / "tests" / "fixtures"):
        return True
    if _is_relative_to(target, project_root / "tests" / "tmp"):
        return True
    return any(part.startswith("pytest-") or part.startswith("pytest-of-") for part in parts)


def _is_real_task_gate_path(target: Path, project_root: Path) -> bool:
    runs_tasks = project_root / "runs" / "tasks"
    if not _is_relative_to(target, runs_tasks):
        return False
    return "gates" in {part.lower() for part in target.parts}


def _is_stage5_2f_smoke_gate_path(target: Path, project_root: Path) -> bool:
    allowed = project_root / "runs" / "tasks" / "stage5_2f_controlled_solver_real_gate_smoke" / "gates"
    return _is_relative_to(target, allowed) or target == allowed


def _is_queue_runtime_status_path(target: Path) -> bool:
    lowered = [part.lower() for part in target.parts]
    return (
        "queue.json" in lowered
        or "live_status.json" in lowered
        or "runtime" in lowered
        or "status" in lowered
        or "queue" in lowered
    )


def _is_source_sanity_base_path(target: Path) -> bool:
    lowered = str(target).lower()
    return "source_sanity_base" in lowered or "sanity_base" in lowered or "source-sanity-base" in lowered


def _absolute(path: Path) -> Path:
    return Path(path).resolve(strict=False)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _result(status: str, target: Path, allowed: bool = False, **extra: Any) -> dict[str, Any]:
    payload = {
        "schema_version": "0.1",
        "stage": "Stage 5.2E",
        "policy_status": status,
        "target_dir": str(target),
        "fixture_mode_required": True,
        "fixture_write_supported": True,
        "stage5_2f_smoke_task_write_supported": True,
        "real_task_write_enabled": False,
        "allowed": allowed,
    }
    payload.update(extra)
    return payload
