from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(r"D:\Projects\AbqPilot-v2")
FORBIDDEN_ROOT = Path(r"D:\Users\wuxia\Documents\AbqPilot")


@dataclass(frozen=True)
class WorkspaceGuardResult:
    path: str
    allowed: bool
    reason: str


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def is_under(path: str | Path, root: str | Path) -> bool:
    resolved = _resolve(path)
    resolved_root = _resolve(root)
    try:
        resolved.relative_to(resolved_root)
        return True
    except ValueError:
        return False


def is_project_root(path: str | Path) -> bool:
    return _resolve(path) == _resolve(PROJECT_ROOT)


def is_forbidden_root(path: str | Path) -> bool:
    return is_under(path, FORBIDDEN_ROOT)


def verify_write_target(path: str | Path, project_root: str | Path = PROJECT_ROOT) -> WorkspaceGuardResult:
    resolved = _resolve(path)
    if is_forbidden_root(resolved):
        return WorkspaceGuardResult(str(resolved), False, "FORBIDDEN_ROOT")
    if not is_under(resolved, project_root):
        return WorkspaceGuardResult(str(resolved), False, "OUTSIDE_PROJECT_ROOT")
    return WorkspaceGuardResult(str(resolved), True, "PROJECT_ROOT_WRITE_ALLOWED")


def is_stage5_3a_cleanup_marker(path: str | Path) -> bool:
    name = str(path).lower()
    return "test_controlled_solver_demo_smoke" in name or "test_stage5_3a_docs.py" in name


def verify_cleanup_target(path: str | Path, forbidden_root: str | Path = FORBIDDEN_ROOT) -> WorkspaceGuardResult:
    resolved = _resolve(path)
    if not is_under(resolved, forbidden_root):
        return WorkspaceGuardResult(str(resolved), False, "NOT_UNDER_FORBIDDEN_ROOT")
    if is_stage5_3a_cleanup_marker(resolved):
        return WorkspaceGuardResult(str(resolved), True, "APPROVED_STAGE5_3A_CLEANUP_TARGET")
    return WorkspaceGuardResult(str(resolved), False, "FORBIDDEN_ROOT_CLEANUP_NOT_APPROVED")


def resolve_project_path(relative_path: str | Path, project_root: str | Path = PROJECT_ROOT) -> Path:
    candidate = _resolve(Path(project_root) / relative_path)
    result = verify_write_target(candidate, project_root)
    if not result.allowed:
        raise ValueError(result.reason)
    return candidate
