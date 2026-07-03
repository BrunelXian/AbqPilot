from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from abqpilot.solver.solver_approval import validate_solver_approval_token
from abqpilot.solver.solver_artifacts import read_json, result, tail_text, write_json
from abqpilot.solver.solver_monitor import classify_solver_run
from abqpilot.solver.solver_preflight import LOCAL_INP_NAME, build_solver_command_preview


def run_solver_approved(
    solver_run_dir: str | Path,
    approval_token: str | Path | None = None,
    timeout_s: int = 7200,
) -> dict[str, Any]:
    run_dir = Path(solver_run_dir)
    preflight = read_json(run_dir / "solver_preflight_result.json")
    validation = validate_solver_approval_token(run_dir, approval_token)
    if not validation.get("valid"):
        details = {
            "solver_launched": False,
            "approval_status": validation.get("status"),
            "errors": validation.get("errors", []),
            "queue_runner_launched": False,
            "abqjobpilot_gui_launched": False,
            "llm_execution_authority": False,
        }
        write_json(run_dir / "solver_run_result.json", details)
        return result("run-solver-approved", "CONTROLLED_SOLVER_RUN_BLOCKED_APPROVAL_REQUIRED", False, run_dir, details)

    command = build_solver_command_preview(
        preflight["command_preview"][0],
        preflight["job_name"],
        LOCAL_INP_NAME,
        int(preflight["cpus"]),
    )
    if command != preflight.get("command_preview"):
        details = {
            "solver_launched": False,
            "errors": ["command preview does not match fixed command structure"],
            "queue_runner_launched": False,
            "abqjobpilot_gui_launched": False,
            "llm_execution_authority": False,
        }
        write_json(run_dir / "solver_run_result.json", details)
        return result("run-solver-approved", "CONTROLLED_SOLVER_RUN_BLOCKED_UNSAFE_COMMAND", False, run_dir, details)

    request = {
        "stage": "Stage 4.0",
        "solver_run_dir": str(run_dir),
        "command": command,
        "cwd": str(run_dir),
        "shell": False,
        "timeout_s": timeout_s,
        "approval_status": validation.get("status"),
    }
    write_json(run_dir / "solver_run_request.json", request)
    run_report: dict[str, Any] = {
        **request,
        "solver_launched": True,
        "queue_runner_launched": False,
        "abqjobpilot_gui_launched": False,
        "llm_execution_authority": False,
        "return_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "expected_odb_path": preflight.get("expected_odb_path"),
        "expected_odb_exists": False,
        "lock_exists_after_completion": False,
        "errors": [],
    }
    run_report.update(execute_controlled_abaqus_command(command, run_dir, timeout_s))

    monitor = classify_solver_run(run_dir)
    run_report["monitor_status"] = monitor["status"]
    run_report["expected_odb_exists"] = bool(monitor.get("odb_exists"))
    run_report["lock_exists_after_completion"] = bool(monitor.get("lock_exists"))
    run_report["sta_tail"] = tail_text(run_dir / f"{preflight.get('job_name')}.sta")
    run_report["msg_tail"] = tail_text(run_dir / f"{preflight.get('job_name')}.msg")
    run_report["dat_tail"] = tail_text(run_dir / f"{preflight.get('job_name')}.dat")
    verdict = (
        "CONTROLLED_SOLVER_RUN_COMPLETED"
        if run_report.get("return_code") == 0 and monitor["status"] == "SOLVER_COMPLETED"
        else "CONTROLLED_SOLVER_RUN_FAILED"
    )
    write_json(run_dir / "solver_run_result.json", run_report)
    return result("run-solver-approved", verdict, verdict == "CONTROLLED_SOLVER_RUN_COMPLETED", run_dir, run_report)


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text


def execute_controlled_abaqus_command(command: list[str], cwd: str | Path, timeout_s: int) -> dict[str, Any]:
    report: dict[str, Any] = {
        "return_code": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "solver_launched": True,
        "errors": [],
    }
    try:
        completed = subprocess.run(
            command,
            cwd=Path(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            shell=False,
        )
        report["return_code"] = completed.returncode
        report["stdout_tail"] = _tail(completed.stdout)
        report["stderr_tail"] = _tail(completed.stderr)
    except subprocess.TimeoutExpired as exc:
        report["return_code"] = None
        report["stdout_tail"] = _tail(exc.stdout or "")
        report["stderr_tail"] = _tail(exc.stderr or "")
        report["errors"].append(f"timeout after {timeout_s}s")
    except OSError as exc:
        report["solver_launched"] = False
        report["errors"].append(str(exc))
    return report
