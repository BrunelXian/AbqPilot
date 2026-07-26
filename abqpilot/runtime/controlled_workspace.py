from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from abqpilot.runtime.context import AbqPilotContext


class WorkspaceViolation(ValueError):
    """Raised when a runtime path escapes its declared workspace scope."""


@dataclass(frozen=True)
class ResolvedWorkspacePath:
    path: Path
    scope: str
    writable: bool


class ControlledWorkspace:
    """Single path authority for runtime reads, writes and execution cwd.

    New production code must request resolved paths through this object rather
    than relying on the process current directory or caller-provided absolute
    paths. Source paths are read-only. Writes are limited to staging, output or
    evidence roots.
    """

    WRITE_SCOPES = {"staging", "output", "evidence"}
    READ_SCOPES = {"project", "source", "staging", "output", "evidence"}

    def __init__(self, context: AbqPilotContext) -> None:
        self.context = context
        self._roots = {
            "project": context.project_root,
            "source": context.source_root,
            "staging": context.staging_root,
            "output": context.output_root,
            "evidence": context.evidence_root,
        }

    @staticmethod
    def _resolve(path: str | Path) -> Path:
        return Path(path).expanduser().resolve(strict=False)

    @staticmethod
    def _is_under(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _root(self, scope: str) -> Path:
        try:
            return self._roots[scope]
        except KeyError as exc:
            raise WorkspaceViolation(f"unknown workspace scope: {scope}") from exc

    def resolve_read(self, path: str | Path, *, scope: str) -> ResolvedWorkspacePath:
        if scope not in self.READ_SCOPES:
            raise WorkspaceViolation(f"scope is not readable: {scope}")
        resolved = self._resolve(path)
        root = self._root(scope)
        if not self._is_under(resolved, root):
            raise WorkspaceViolation(f"READ_OUTSIDE_{scope.upper()}_ROOT: {resolved}")
        return ResolvedWorkspacePath(resolved, scope, False)

    def resolve_write(self, path: str | Path, *, scope: str) -> ResolvedWorkspacePath:
        if scope not in self.WRITE_SCOPES:
            raise WorkspaceViolation(f"scope is not writable: {scope}")
        resolved = self._resolve(path)
        root = self._root(scope)
        if not self._is_under(resolved, root):
            raise WorkspaceViolation(f"WRITE_OUTSIDE_{scope.upper()}_ROOT: {resolved}")
        if self._is_under(resolved, self.context.source_root) and self.context.source_root not in {
            self.context.staging_root,
            self.context.output_root,
            self.context.evidence_root,
        }:
            raise WorkspaceViolation(f"IMMUTABLE_SOURCE_WRITE: {resolved}")
        return ResolvedWorkspacePath(resolved, scope, True)

    def resolve_execution_cwd(self, path: str | Path) -> Path:
        resolved = self._resolve(path)
        allowed_roots = (self.context.staging_root, self.context.output_root)
        if not any(self._is_under(resolved, root) for root in allowed_roots):
            raise WorkspaceViolation(f"EXECUTION_CWD_OUTSIDE_RUNTIME_ROOTS: {resolved}")
        return resolved

    def ensure_directory(self, path: str | Path, *, scope: str) -> Path:
        resolved = self.resolve_write(path, scope=scope).path
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved
