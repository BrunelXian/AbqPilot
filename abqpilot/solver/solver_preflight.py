from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from abqpilot.core.hash_utils import sha256_file, sha256_json_obj
from abqpilot.solver.solver_artifacts import result, timestamp, write_json, write_text
from abqpilot.solver.solver_candidate import validate_solver_candidate


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGE4_ROOT = PROJECT_ROOT / "runs" / "stage4_0_controlled_solver_automation"
DEFAULT_ABAQUS_COMMAND = r"D:\ABAQUS2024\Commands\abq2024.bat"
JOB_NAME = "candidate_sanity_base_power_x2_stage4"
LOCAL_INP_NAME = f"{JOB_NAME}.inp"


def prepare_solver_run(
    candidate_inp: str | Path,
    source_inp: str | Path,
    evidence_dir: str | Path,
    cpus: int = 14,
    run_root: str | Path = DEFAULT_STAGE4_ROOT,
    abaqus_command: str | Path = DEFAULT_ABAQUS_COMMAND,
) -> dict[str, Any]:
    root = Path(run_root)
    solver_run_dir = root / ("run_" + timestamp())
    solver_run_dir.mkdir(parents=True, exist_ok=False)
    expected_odb = solver_run_dir / f"{JOB_NAME}.odb"
    local_inp = solver_run_dir / LOCAL_INP_NAME
    validation = validate_solver_candidate(candidate_inp, source_inp, evidence_dir, solver_run_dir, JOB_NAME, int(cpus))

    preflight_request = {
        "stage": "Stage 4.0",
        "candidate_inp_path": str(Path(candidate_inp)),
        "source_inp_path": str(Path(source_inp)),
        "evidence_dir": str(Path(evidence_dir)),
        "solver_run_dir": str(solver_run_dir),
        "job_name": JOB_NAME,
        "cpus": int(cpus),
        "abaqus_command": str(abaqus_command),
    }
    write_json(solver_run_dir / "solver_preflight_request.json", preflight_request)

    if not validation["eligible"]:
        preflight_result = {
            **preflight_request,
            **validation,
            "eligible_for_solver": False,
            "requires_human_approval": False,
        }
        _write_preflight_artifacts(solver_run_dir, preflight_result, {}, "")
        return result("prepare-solver-run", validation["verdict"], False, solver_run_dir, preflight_result)

    shutil.copyfile(candidate_inp, local_inp)
    command_preview = build_solver_command_preview(abaqus_command, JOB_NAME, LOCAL_INP_NAME, int(cpus))
    command_text = " ".join(f'"{arg}"' if " " in str(arg) else str(arg) for arg in command_preview)
    preflight_result = {
        "stage": "Stage 4.0",
        "candidate_traceability": "sanity-base-derived",
        "candidate_inp_path": str(Path(candidate_inp)),
        "local_candidate_inp_path": str(local_inp),
        "candidate_inp_sha256": validation["candidate_inp_sha256"],
        "source_inp_path": str(Path(source_inp)),
        "source_inp_sha256": validation["source_inp_sha256"],
        "solver_run_dir": str(solver_run_dir),
        "job_name": JOB_NAME,
        "expected_odb_path": str(expected_odb),
        "cpus": int(cpus),
        "static_validator_status": validation["static_validator_status"],
        "diff_guard_status": validation["diff_guard_status"],
        "physics_guard_status": validation["physics_guard_status"],
        "unrelated_changes_count": validation["unrelated_changes_count"],
        "changed_lines_count": validation["changed_lines_count"],
        "exact_patch_operation": validation["exact_patch_operation"],
        "fixture_only": False,
        "eligible_for_solver": True,
        "requires_human_approval": True,
        "command_preview": command_preview,
        "command_preview_text": command_text,
        "abaqus_command_preview_sha256": sha256_json_obj({"command": command_preview}),
        "solver_submitted": False,
        "queue_runner_launched": False,
        "llm_execution_authority": False,
        "errors": [],
        "warnings": [],
    }
    approval_request = create_solver_approval_request(preflight_result)
    _write_preflight_artifacts(solver_run_dir, preflight_result, approval_request, command_text)
    return result("prepare-solver-run", "SOLVER_RUN_PREPARED", True, solver_run_dir, preflight_result)


def build_solver_command_preview(abaqus_command: str | Path, job_name: str, input_name: str, cpus: int) -> list[str]:
    if int(cpus) < 1 or int(cpus) > 14:
        raise ValueError("cpus must be between 1 and 14")
    if input_name != LOCAL_INP_NAME:
        raise ValueError("input filename must be the local copied candidate INP")
    return [str(abaqus_command), f"job={job_name}", f"input={input_name}", f"cpus={int(cpus)}", "interactive"]


def create_solver_approval_request(preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "approval_type": "abqpilot_controlled_solver_run",
        "stage": "Stage 4.0",
        "status": "APPROVAL_REQUIRED",
        "candidate_inp_path": preflight["local_candidate_inp_path"],
        "candidate_inp_sha256": preflight["candidate_inp_sha256"],
        "source_inp_sha256": preflight["source_inp_sha256"],
        "solver_run_dir": preflight["solver_run_dir"],
        "job_name": preflight["job_name"],
        "expected_odb_path": preflight["expected_odb_path"],
        "abaqus_command_preview_sha256": preflight["abaqus_command_preview_sha256"],
        "cpus": preflight["cpus"],
        "static_validator_status": preflight["static_validator_status"],
        "diff_guard_status": preflight["diff_guard_status"],
        "physics_guard_status": preflight["physics_guard_status"],
        "unrelated_changes_count": preflight["unrelated_changes_count"],
        "required_conditions": {
            "candidate_traceability": "sanity-base-derived",
            "allow_solver_submit": True,
            "queue_runner_allowed": False,
            "llm_execution_authority": False,
        },
    }


def _write_preflight_artifacts(solver_run_dir: Path, preflight_result: dict[str, Any], approval_request: dict[str, Any], command_text: str) -> None:
    manifest = {
        "schema_version": "0.1",
        "stage": "Stage 4.0",
        "candidate_inp_path": preflight_result.get("local_candidate_inp_path") or preflight_result.get("candidate_inp_path"),
        "candidate_inp_sha256": preflight_result.get("candidate_inp_sha256"),
        "source_inp_path": preflight_result.get("source_inp_path"),
        "source_inp_sha256": preflight_result.get("source_inp_sha256"),
        "job_name": preflight_result.get("job_name"),
        "expected_odb_path": preflight_result.get("expected_odb_path"),
        "eligible_for_solver": preflight_result.get("eligible_for_solver", False),
        "requires_human_approval": preflight_result.get("requires_human_approval", False),
    }
    write_json(solver_run_dir / "solver_candidate_manifest.json", manifest)
    write_json(solver_run_dir / "solver_preflight_result.json", preflight_result)
    write_json(solver_run_dir / "solver_command_preview.json", {"command": preflight_result.get("command_preview", [])})
    write_text(solver_run_dir / "solver_command_preview.txt", command_text + "\n" if command_text else "")
    if approval_request:
        write_json(solver_run_dir / "solver_approval_request.json", approval_request)
