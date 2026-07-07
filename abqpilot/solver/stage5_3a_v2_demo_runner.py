from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

ABAQUS_COMMAND = r"D:\ABAQUS2024\Commands\abq2024.bat"
TASK_ID = "stage5_3a_v2_controlled_solver_demo_smoke"
JOB_NAME = "stage5_3a_v2_demo_solver_smoke"
CPU_COUNT = 4
TIMEOUT_SECONDS = 1800


def build_stage5_3a_v2_demo_command(candidate_inp: str | Path) -> list[str]:
    inp = Path(candidate_inp).resolve(strict=False)
    return [ABAQUS_COMMAND, f"job={JOB_NAME}", f"input={inp}", f"cpus={CPU_COUNT}", "interactive"]


def execute_stage5_3a_v2_demo_solver_request(request: dict[str, Any]) -> dict[str, Any]:
    command_path = Path(str(request.get("solver_command_path", "")))
    inp = Path(str(request.get("candidate_inp_path", "")))
    work_dir = Path(str(request.get("working_directory", "")))
    timeout = int(request.get("timeout_seconds") or TIMEOUT_SECONDS)
    command = build_stage5_3a_v2_demo_command(inp)
    if str(command_path) != ABAQUS_COMMAND or command[0] != ABAQUS_COMMAND:
        return _blocked("STAGE5_3A_V2_BLOCKED_UNSAFE_COMMAND_SHAPE", command, work_dir, timeout)
    if request.get("task_id") != TASK_ID:
        return _blocked("STAGE5_3A_V2_BLOCKED_ARBITRARY_TASK_PATH", command, work_dir, timeout)
    if request.get("smoke_demo_only") is not True or request.get("arbitrary_task_execution_allowed") is not False:
        return _blocked("STAGE5_3A_V2_BLOCKED_ARBITRARY_TASK_PATH", command, work_dir, timeout)
    if request.get("solver_execution_allowed") is not True or request.get("executable_request") is not True:
        return _blocked("STAGE5_3A_V2_BLOCKED_REQUEST_NOT_EXECUTABLE_FOR_DEMO", command, work_dir, timeout)
    if not command_path.exists():
        return _blocked("STAGE5_3A_V2_BLOCKED_ABAQUS_COMMAND_NOT_FOUND", command, work_dir, timeout)
    if not inp.exists():
        return _blocked("STAGE5_3A_V2_BLOCKED_DEMO_INP_NOT_FOUND", command, work_dir, timeout)
    work_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"solver_invoked": True, "command_args": command, "command_is_list": True, "shell": False, "cwd": str(work_dir), "timeout_seconds": timeout, "solver_return_code": None, "timed_out": False, "stdout_tail": "", "stderr_tail": "", "errors": []}
    try:
        completed = subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout, shell=False)
        report["solver_return_code"] = completed.returncode
        report["stdout_tail"] = _tail(completed.stdout)
        report["stderr_tail"] = _tail(completed.stderr)
        report["solver_status"] = "STAGE5_3A_V2_SOLVER_RUN_COMPLETED_RETURN_ZERO" if completed.returncode == 0 else "STAGE5_3A_V2_SOLVER_RUN_COMPLETED_NONZERO_RETURN"
    except subprocess.TimeoutExpired as exc:
        report["timed_out"] = True
        report["stdout_tail"] = _tail(exc.stdout or "")
        report["stderr_tail"] = _tail(exc.stderr or "")
        report["solver_status"] = "STAGE5_3A_V2_SOLVER_RUN_TIMED_OUT"
    except OSError as exc:
        report["solver_invoked"] = False
        report["errors"].append(str(exc))
        report["solver_status"] = "STAGE5_3A_V2_SOLVER_RUN_OS_ERROR"
    return report


def _blocked(status: str, command: list[str], work_dir: Path, timeout: int) -> dict[str, Any]:
    return {"solver_invoked": False, "command_args": command, "command_is_list": True, "shell": False, "cwd": str(work_dir), "timeout_seconds": timeout, "solver_return_code": None, "timed_out": False, "stdout_tail": "", "stderr_tail": "", "errors": [status], "solver_status": status}


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text
