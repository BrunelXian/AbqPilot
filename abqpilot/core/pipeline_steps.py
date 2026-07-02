from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.core.approval import approval_token_path, create_approval_request, validate_approval_token
from abqpilot.core.hash_utils import sha256_file
from abqpilot.core.task_result import make_task_result


STEP_NAMES = [
    "01_export_cae",
    "02_audit_heat_x2",
    "03_abqjobpilot_preflight",
    "04_abqjobpilot_dry_run_enqueue",
    "05_jobpilot_enqueue_authorization",
    "06_abqjobpilot_real_enqueue",
    "07_abqjobpilot_status_poll",
    "08_solver_intake",
    "09_odb_metrics",
    "10_compare_metrics",
]


def run_pipeline_step(step_name: str, context: dict[str, Any]) -> dict[str, Any]:
    if step_name == "01_export_cae":
        return step_export_cae(context)
    if step_name == "02_audit_heat_x2":
        return step_audit_heat_x2(context)
    if step_name == "03_abqjobpilot_preflight":
        return step_abqjobpilot_preflight(context)
    if step_name == "04_abqjobpilot_dry_run_enqueue":
        return step_abqjobpilot_dry_run_enqueue(context)
    if step_name == "05_jobpilot_enqueue_authorization":
        return step_jobpilot_enqueue_authorization(context)
    if step_name == "06_abqjobpilot_real_enqueue":
        return step_abqjobpilot_real_enqueue(context)
    if step_name == "07_abqjobpilot_status_poll":
        return step_abqjobpilot_status_poll(context)
    if step_name == "08_solver_intake":
        return step_solver_intake(context)
    if step_name == "09_odb_metrics":
        return step_odb_metrics(context)
    if step_name == "10_compare_metrics":
        return step_compare_metrics(context)
    raise ValueError(f"unknown pipeline step: {step_name}")


def step_export_cae(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.cli import command_export_cae

    config = context["config"]
    step_dir = context["step_dir"]
    result = command_export_cae(
        cae=config["cae_path"],
        out_dir=step_dir,
        job_name=config.get("export_job_name", "sanity_base_v01_export"),
        config_path=context["config_path"],
    )
    existing_inp = config.get("existing_exported_inp_path")
    if existing_inp and Path(existing_inp).exists() and not Path(result["output_paths"].get("expected_inp_path", "")).exists():
        result["output_paths"]["expected_inp_path"] = str(Path(existing_inp))
        result["details"]["reused_existing_exported_inp"] = str(Path(existing_inp))
        if result["verdict"] == "CAE_EXPORT_DISABLED":
            result["verdict"] = "CAE_EXPORT_DISABLED_REUSED_EXISTING_INP"
            result["success"] = True
    result["command"] = "01_export_cae"
    return result


def step_audit_heat_x2(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.cli import command_audit_heat_x2

    exported_inp = context.get("exported_inp_path")
    if not exported_inp or not Path(exported_inp).exists():
        return make_task_result(
            command="02_audit_heat_x2",
            verdict="NEED_EXPORTED_INP",
            success=False,
            safety_flags=context["safety_flags"],
            errors=["exported INP is required before heat audit"],
        )
    result = command_audit_heat_x2(
        source_inp=exported_inp,
        out_dir=context["step_dir"],
        scale=float(context["config"].get("heat_input_scale", 2.0)),
    )
    result["command"] = "02_audit_heat_x2"
    return result


def step_solver_intake(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.cli import command_intake_solver

    config = context["config"]
    search_root = config.get("solver_search_root") or Path(config.get("work_root", "runs")).parent / "CAE_model" / "sanity_base"
    result = command_intake_solver(search_root=search_root, out_dir=context["step_dir"])
    result["command"] = "08_solver_intake"
    if result["verdict"] in {"FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND", "FAIL_ODB_PAIR_NOT_FOUND"}:
        result["verdict"] = "NEED_MANUAL_SOLVER_OUTPUTS"
        result["success"] = False
    return result


def step_odb_metrics(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.cli import command_extract_odb_metrics

    contract = context.get("odb_contract_path")
    if not contract or not Path(contract).exists():
        return make_task_result(
            command="09_odb_metrics",
            verdict="NEED_MANUAL_SOLVER_OUTPUTS",
            success=False,
            safety_flags=context["safety_flags"],
            errors=["ODB metrics contract is missing"],
        )
    result = command_extract_odb_metrics(
        contract=contract,
        out_dir=context["step_dir"],
        config_path=context["config_path"],
    )
    result["command"] = "09_odb_metrics"
    if result["verdict"] == "FAIL_ODB_PAIR_NOT_FOUND":
        result["verdict"] = "NEED_MANUAL_SOLVER_OUTPUTS"
        result["success"] = False
    elif result["verdict"] == "ODB_READ_DISABLED":
        result["verdict"] = "NEED_ODB_METRICS_JSON"
        result["success"] = False
    return result


def step_compare_metrics(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.cli import command_compare_metrics

    metrics_path = context.get("metrics_json_path")
    if not metrics_path or not Path(metrics_path).exists():
        return make_task_result(
            command="10_compare_metrics",
            verdict="NEED_ODB_METRICS_JSON",
            success=False,
            safety_flags=context["safety_flags"],
            errors=["metrics JSON is required before comparison"],
        )
    result = command_compare_metrics(metrics=metrics_path, out_dir=context["step_dir"])
    result["command"] = "10_compare_metrics"
    return result


def step_abqjobpilot_preflight(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.integrations import AbqJobPilotPreflightAdapter

    config = context["config"]
    if config.get("skip_jobpilot_preflight") or not config.get("allow_abqjobpilot_preflight", False):
        return make_task_result(
            command="03_abqjobpilot_preflight",
            verdict="SKIPPED_JOBPILOT_PREFLIGHT",
            success=True,
            safety_flags=context["safety_flags"],
            warnings=["abqjobpilot preflight step skipped by configuration"],
        )

    candidate_inp = context.get("candidate_inp_path")
    if not candidate_inp or not Path(candidate_inp).exists():
        return make_task_result(
            command="03_abqjobpilot_preflight",
            verdict="NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT",
            success=False,
            safety_flags=context["safety_flags"],
            errors=["candidate INP is required for abqjobpilot preflight"],
        )

    jobpilot_config = config.get("jobpilot", {})
    abqjobpilot_config = config.get("abqjobpilot", {})
    project_root = abqjobpilot_config.get("project_root")
    adapter = AbqJobPilotPreflightAdapter(project_root=project_root)
    request = adapter.build_request(
        inp_path=str(candidate_inp),
        job_name=abqjobpilot_config.get("job_name") or jobpilot_config.get("job_name") or Path(candidate_inp).stem,
        cpus=int(abqjobpilot_config.get("cpus", jobpilot_config.get("cpus", 14))),
        batch=abqjobpilot_config.get("batch", jobpilot_config.get("batch", "sanity_base_heat_x2")),
        strategy=abqjobpilot_config.get("strategy", jobpilot_config.get("strategy", "power_x2")),
        working_dir=abqjobpilot_config.get("working_dir") or jobpilot_config.get("working_dir") or str(Path(candidate_inp).parent),
        metadata={"source": "AbqPilot-v2", "task_id": context.get("task_id")},
    )
    preflight_result = adapter.preflight(request)
    artifact_paths = adapter.write_preflight_artifacts(request, preflight_result, str(context["step_dir"]))
    verdict = preflight_result.get("status", "PREVIEW_READY")
    return make_task_result(
        command="03_abqjobpilot_preflight",
        verdict=verdict,
        success=verdict in {"PREVIEW_READY", "ABQJOBPILOT_UNAVAILABLE"},
        output_paths=artifact_paths,
        safety_flags=context["safety_flags"],
        warnings=preflight_result.get("warnings", []),
        errors=[] if verdict == "ABQJOBPILOT_UNAVAILABLE" else preflight_result.get("errors", []),
        details={"request": request, "preflight_result": preflight_result, "availability": adapter.diagnostics()},
    )


def step_abqjobpilot_dry_run_enqueue(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.integrations import AbqJobPilotPreflightAdapter

    config = context["config"]
    if config.get("skip_jobpilot_dry_run_enqueue") or not config.get("allow_abqjobpilot_dry_run_enqueue", False):
        return make_task_result(
            command="04_abqjobpilot_dry_run_enqueue",
            verdict="SKIPPED_JOBPILOT_DRY_RUN_ENQUEUE",
            success=True,
            safety_flags=context["safety_flags"],
            warnings=["abqjobpilot dry-run enqueue step skipped by configuration"],
        )

    request_path = context.get("abqjobpilot_request_path")
    if not request_path or not Path(request_path).exists():
        return make_task_result(
            command="04_abqjobpilot_dry_run_enqueue",
            verdict="NEED_JOBPILOT_PREFLIGHT_REQUEST",
            success=False,
            safety_flags=context["safety_flags"],
            errors=["abqjobpilot preflight request is required before dry-run enqueue"],
        )

    request = _read_json(request_path)
    abqjobpilot_config = config.get("abqjobpilot", {})
    adapter = AbqJobPilotPreflightAdapter(project_root=abqjobpilot_config.get("project_root"))
    dry_run_result = adapter.dry_run_enqueue(request)
    artifact_paths = adapter.write_dry_run_enqueue_artifacts(request, dry_run_result, str(context["step_dir"]))
    verdict = dry_run_result.get("status", "DRY_RUN_READY")
    return make_task_result(
        command="04_abqjobpilot_dry_run_enqueue",
        verdict=verdict,
        success=verdict in {"DRY_RUN_READY", "ABQJOBPILOT_UNAVAILABLE"},
        output_paths=artifact_paths,
        safety_flags=context["safety_flags"],
        warnings=dry_run_result.get("warnings", []),
        errors=[] if verdict == "ABQJOBPILOT_UNAVAILABLE" else dry_run_result.get("errors", []),
        details={"request": request, "dry_run_result": dry_run_result, "availability": adapter.diagnostics()},
    )


def step_jobpilot_enqueue_authorization(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.core.approval import request_conditions_are_safe, write_authorization_artifacts

    if not context["config"].get("allow_jobpilot_enqueue_authorization", False):
        return make_task_result(
            command="05_jobpilot_enqueue_authorization",
            verdict="SKIPPED_JOBPILOT_ENQUEUE_AUTHORIZATION",
            success=True,
            safety_flags=context["safety_flags"],
            warnings=["jobpilot enqueue authorization gate skipped by configuration"],
        )

    required_paths = {
        "candidate_inp_path": context.get("candidate_inp_path"),
        "abqjobpilot_request_path": context.get("abqjobpilot_request_path"),
        "abqjobpilot_preflight_result_path": context.get("abqjobpilot_preflight_result_path"),
        "abqjobpilot_dry_run_result_path": context.get("abqjobpilot_dry_run_result_path"),
    }
    missing = [name for name, value in required_paths.items() if not value or not Path(value).exists()]
    if missing:
        return make_task_result(
            command="05_jobpilot_enqueue_authorization",
            verdict="NEED_JOBPILOT_AUTHORIZATION_EVIDENCE",
            success=False,
            safety_flags=context["safety_flags"],
            errors=[f"missing authorization evidence: {', '.join(missing)}"],
        )

    request = create_approval_request(
        task_id=context["task_id"],
        step_dir=context["step_dir"],
        candidate_inp_path=required_paths["candidate_inp_path"],
        job_request_path=required_paths["abqjobpilot_request_path"],
        preflight_result_path=required_paths["abqjobpilot_preflight_result_path"],
        dry_run_result_path=required_paths["abqjobpilot_dry_run_result_path"],
    )
    safe, safety_errors = request_conditions_are_safe(request)
    token_path = approval_token_path(context["task_dir"])
    validation = validate_approval_token(request, token_path)
    artifact_paths = write_authorization_artifacts(context["step_dir"], request, validation)
    if token_path.exists():
        artifact_paths["jobpilot_enqueue_approval_token"] = str(token_path)

    verdict = "APPROVAL_REQUIRED" if validation["status"] == "APPROVAL_TOKEN_MISSING" else validation["status"]
    errors = safety_errors if not safe else ([] if verdict == "APPROVAL_REQUIRED" else validation.get("errors", []))
    return make_task_result(
        command="05_jobpilot_enqueue_authorization",
        verdict=verdict,
        success=verdict in {"APPROVAL_REQUIRED", "APPROVAL_TOKEN_VALID"},
        output_paths=artifact_paths,
        safety_flags=context["safety_flags"],
        warnings=[] if verdict != "APPROVAL_REQUIRED" else ["human approval token has not been created"],
        errors=errors,
        details={"approval_request": request, "authorization_validation": validation},
    )


def step_abqjobpilot_real_enqueue(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.integrations import AbqJobPilotPreflightAdapter

    config = context["config"]
    if config.get("skip_real_jobpilot_enqueue"):
        abqjobpilot_config = config.get("abqjobpilot", {})
        adapter = AbqJobPilotPreflightAdapter(project_root=abqjobpilot_config.get("project_root"))
        request = _read_json(context["abqjobpilot_request_path"]) if context.get("abqjobpilot_request_path") else {}
        result = {
            "status": "SKIPPED_REAL_JOBPILOT_ENQUEUE",
            "queue_mutated": False,
            "forbidden_mutation_detected": False,
            "errors": [],
            "warnings": ["real abqjobpilot enqueue step skipped by configuration"],
        }
        artifact_paths = adapter.write_real_enqueue_artifacts(request, result, str(context["step_dir"]))
        return make_task_result(
            command="06_abqjobpilot_real_enqueue",
            verdict="SKIPPED_REAL_JOBPILOT_ENQUEUE",
            success=True,
            output_paths=artifact_paths,
            safety_flags=context["safety_flags"],
            warnings=["real abqjobpilot enqueue step skipped by configuration"],
        )

    abqjobpilot_config = config.get("abqjobpilot", {})
    adapter = AbqJobPilotPreflightAdapter(project_root=abqjobpilot_config.get("project_root"))
    if not config.get("allow_abqjobpilot_real_enqueue", False):
        request = _read_json(context["abqjobpilot_request_path"]) if context.get("abqjobpilot_request_path") else {}
        result = adapter.real_enqueue(
            request,
            {
                "allow_abqjobpilot_real_enqueue": False,
                "approval_token_status": "APPROVAL_TOKEN_VALID",
                "preflight_status": "PREVIEW_READY",
                "dry_run_enqueue_status": "DRY_RUN_READY",
                "runtime_mutation_detected": False,
                "allow_solver_submit": False,
                "submission_mode": "preview_only",
                "candidate_inp_sha256_matches": True,
                "job_request_sha256_matches": True,
                "preflight_result_sha256_matches": True,
                "dry_run_result_sha256_matches": True,
                "queue_only_confirmed": False,
            },
        )
        artifact_paths = adapter.write_real_enqueue_artifacts(request, result, str(context["step_dir"]))
        return make_task_result(
            command="06_abqjobpilot_real_enqueue",
            verdict=result["status"],
            success=True,
            output_paths=artifact_paths,
            safety_flags=context["safety_flags"],
            warnings=["real abqjobpilot enqueue is disabled by configuration"],
            errors=[],
            details={"real_enqueue_result": result},
        )

    required_paths = {
        "candidate_inp_path": context.get("candidate_inp_path"),
        "abqjobpilot_request_path": context.get("abqjobpilot_request_path"),
        "abqjobpilot_preflight_result_path": context.get("abqjobpilot_preflight_result_path"),
        "abqjobpilot_dry_run_result_path": context.get("abqjobpilot_dry_run_result_path"),
        "jobpilot_enqueue_authorization_report_path": context.get("jobpilot_enqueue_authorization_report_path"),
    }
    missing = [name for name, value in required_paths.items() if not value or not Path(value).exists()]
    request = _read_json(required_paths["abqjobpilot_request_path"]) if not missing else {}
    if missing:
        result = {
            "status": "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE",
            "errors": [f"missing real enqueue evidence: {', '.join(missing)}"],
            "warnings": [],
            "queue_mutated": False,
            "forbidden_mutation_detected": False,
        }
        artifact_paths = adapter.write_real_enqueue_artifacts(request, result, str(context["step_dir"]))
        return make_task_result(
            command="06_abqjobpilot_real_enqueue",
            verdict=result["status"],
            success=False,
            output_paths=artifact_paths,
            safety_flags=context["safety_flags"],
            errors=result["errors"],
            details={"real_enqueue_result": result},
        )

    approval_report = _build_real_enqueue_approval_report(context, config)
    result = adapter.real_enqueue(request, approval_report)
    artifact_paths = adapter.write_real_enqueue_artifacts(request, result, str(context["step_dir"]))
    verdict = result.get("status", "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE")
    return make_task_result(
        command="06_abqjobpilot_real_enqueue",
        verdict=verdict,
        success=verdict
        in {
            "REAL_ENQUEUE_COMPLETED",
            "REAL_ENQUEUE_REJECTED_CONFIG_DISABLED",
            "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE",
            "REAL_ENQUEUE_REJECTED_UNSAFE_DIRECT_SUBMIT",
            "ABQJOBPILOT_UNAVAILABLE",
        },
        output_paths=artifact_paths,
        safety_flags=context["safety_flags"],
        warnings=result.get("warnings", []),
        errors=result.get("errors", []),
        details={"approval_report": approval_report, "real_enqueue_result": result},
    )


def step_abqjobpilot_status_poll(context: dict[str, Any]) -> dict[str, Any]:
    from abqpilot.integrations import AbqJobPilotPreflightAdapter, normalize_jobpilot_status

    config = context["config"]
    real_enqueue_result = _read_json(context["abqjobpilot_real_enqueue_result_path"]) if context.get("abqjobpilot_real_enqueue_result_path") and Path(context["abqjobpilot_real_enqueue_result_path"]).exists() else {}
    poll_requested = bool(config.get("poll_jobpilot_status") or config.get("jobpilot_job_id"))
    real_enqueue_completed = real_enqueue_result.get("status") == "REAL_ENQUEUE_COMPLETED"
    if (
        config.get("skip_jobpilot_status_poll")
        or not config.get("allow_abqjobpilot_status_poll", False)
        or (not poll_requested and not real_enqueue_completed)
    ):
        return make_task_result(
            command="07_abqjobpilot_status_poll",
            verdict="SKIPPED_JOBPILOT_STATUS_POLL",
            success=True,
            safety_flags=context["safety_flags"],
            warnings=["abqjobpilot status poll step skipped by configuration"],
        )

    job_id = config.get("jobpilot_job_id") or real_enqueue_result.get("job_id")
    if not job_id:
        return make_task_result(
            command="07_abqjobpilot_status_poll",
            verdict="NEED_ABQJOBPILOT_JOB_ID",
            success=False,
            safety_flags=context["safety_flags"],
            errors=["abqjobpilot job_id is required before status polling"],
        )

    abqjobpilot_config = config.get("abqjobpilot", {})
    adapter = AbqJobPilotPreflightAdapter(project_root=abqjobpilot_config.get("project_root"))
    status_result = adapter.poll_status(job_id=job_id)
    output_result = adapter.locate_outputs(job_id=job_id)
    status_result["task_id"] = context.get("task_id")
    output_result["task_id"] = context.get("task_id")
    normalized = normalize_jobpilot_status(status_result, output_result)
    status_result["normalized_status"] = normalized
    output_result["normalized_status"] = normalized
    artifact_paths = adapter.write_status_artifacts(status_result, output_result, str(context["step_dir"]))
    verdict = normalized
    errors = list(status_result.get("errors", [])) + list(output_result.get("errors", []))
    warnings = list(status_result.get("warnings", [])) + list(output_result.get("warnings", []))
    return make_task_result(
        command="07_abqjobpilot_status_poll",
        verdict=verdict,
        success=verdict
        in {
            "JOB_QUEUED",
            "JOB_RUNNING",
            "JOB_COMPLETED",
            "JOB_FAILED",
            "JOB_LOCKED",
            "JOB_ODB_MISSING",
            "JOB_OUTPUTS_READY",
            "JOB_UNKNOWN",
            "ABQJOBPILOT_UNAVAILABLE",
        },
        output_paths=artifact_paths,
        safety_flags=context["safety_flags"],
        warnings=warnings,
        errors=[] if verdict == "ABQJOBPILOT_UNAVAILABLE" else errors,
        details={
            "job_id": job_id,
            "raw_status": status_result.get("status"),
            "normalized_status": normalized,
            "status_result": status_result,
            "output_result": output_result,
        },
    )


def _build_real_enqueue_approval_report(context: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    candidate = context["candidate_inp_path"]
    request_path = context["abqjobpilot_request_path"]
    preflight_path = context["abqjobpilot_preflight_result_path"]
    dry_run_path = context["abqjobpilot_dry_run_result_path"]
    token_path = approval_token_path(context["task_dir"])
    approval_request = create_approval_request(
        task_id=context["task_id"],
        step_dir=context["step_dir"],
        candidate_inp_path=candidate,
        job_request_path=request_path,
        preflight_result_path=preflight_path,
        dry_run_result_path=dry_run_path,
    )
    validation = validate_approval_token(approval_request, token_path)
    request = _read_json(request_path)
    preflight = _read_json(preflight_path)
    dry_run = _read_json(dry_run_path)
    token = _read_json(token_path) if token_path.exists() else {}
    abqjobpilot_config = config.get("abqjobpilot", {})
    return {
        "approval_token_status": validation["status"],
        "allow_abqjobpilot_real_enqueue": bool(config.get("allow_abqjobpilot_real_enqueue", False)),
        "allow_solver_submit": bool(request.get("allow_solver_submit")),
        "submission_mode": request.get("submission_mode"),
        "preflight_status": preflight.get("status"),
        "dry_run_enqueue_status": dry_run.get("status"),
        "runtime_mutation_detected": bool(dry_run.get("runtime_mutation_detected")),
        "candidate_inp_sha256_matches": token.get("candidate_inp_sha256") == sha256_file(candidate),
        "job_request_sha256_matches": token.get("job_request_sha256") == sha256_file(request_path),
        "preflight_result_sha256_matches": token.get("preflight_result_sha256") == sha256_file(preflight_path),
        "dry_run_result_sha256_matches": token.get("dry_run_result_sha256") == sha256_file(dry_run_path),
        "queue_only_confirmed": bool(abqjobpilot_config.get("queue_only_confirmed", False)),
        "dry_run_result": dry_run,
        "authorization_validation": validation,
        "authorization_report": _read_json(context["jobpilot_enqueue_authorization_report_path"]),
    }


def _read_json(path: str | Path) -> dict[str, Any]:
    import json

    return json.loads(Path(path).read_text(encoding="utf-8"))


def _job_id_from_real_enqueue_result(path: str | Path | None) -> str | None:
    if not path or not Path(path).exists():
        return None
    try:
        payload = _read_json(path)
    except Exception:
        return None
    return payload.get("job_id")
