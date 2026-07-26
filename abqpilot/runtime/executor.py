from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from abqpilot.runtime.context import AbqPilotContext
from abqpilot.runtime.controlled_workspace import ControlledWorkspace


@dataclass(frozen=True)
class ExecutionRequest:
    tool_name: str
    command: tuple[str, ...]
    cwd: Path
    timeout_s: int
    authorization_id: str
    risk_level: str = "L2"

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("tool_name must not be empty")
        if not self.command or not all(str(part).strip() for part in self.command):
            raise ValueError("command must contain non-empty arguments")
        if self.timeout_s < 1:
            raise ValueError("timeout_s must be at least 1")
        if not self.authorization_id.strip():
            raise ValueError("authorization_id must not be empty")
        object.__setattr__(self, "cwd", Path(self.cwd).expanduser().resolve(strict=False))


@dataclass(frozen=True)
class ExecutionResult:
    return_code: int | None
    stdout_tail: str = ""
    stderr_tail: str = ""
    process_started: bool = False
    errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        return {
            "return_code": self.return_code,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "solver_launched": self.process_started,
            "errors": list(self.errors),
        }


CompletedProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


class ControlledExecutor:
    """The only production subprocess boundary for AbqPilot runtime tools."""

    def __init__(
        self,
        context: AbqPilotContext,
        workspace: ControlledWorkspace | None = None,
        *,
        process_runner: CompletedProcessRunner = subprocess.run,
    ) -> None:
        self.context = context
        self.workspace = workspace or ControlledWorkspace(context)
        self._process_runner = process_runner

    @staticmethod
    def _tail(text: str, limit: int = 4000) -> str:
        return text[-limit:] if len(text) > limit else text

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.tool_name not in self.context.allowed_tools:
            raise PermissionError(f"tool is not allowed by runtime context: {request.tool_name}")
        cwd = self.workspace.resolve_execution_cwd(request.cwd)
        expected_command = str(self.context.abaqus_command)
        if str(request.command[0]) != expected_command:
            raise PermissionError("command executable does not match resolved runtime context")

        try:
            completed = self._process_runner(
                list(request.command),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=request.timeout_s,
                shell=False,
            )
            return ExecutionResult(
                return_code=completed.returncode,
                stdout_tail=self._tail(completed.stdout or ""),
                stderr_tail=self._tail(completed.stderr or ""),
                process_started=True,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                return_code=None,
                stdout_tail=self._tail(exc.stdout or ""),
                stderr_tail=self._tail(exc.stderr or ""),
                process_started=True,
                errors=(f"timeout after {request.timeout_s}s",),
            )
        except OSError as exc:
            return ExecutionResult(return_code=None, process_started=False, errors=(str(exc),))
