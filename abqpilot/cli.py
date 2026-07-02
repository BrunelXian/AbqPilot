from __future__ import annotations

import argparse
import json
from importlib import metadata
from pathlib import Path
from typing import Any

from abqpilot.analysis import build_agent_observation, build_comparison_report
from abqpilot.analysis.metrics_comparator import render_markdown_report
from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder
from abqpilot.cae import CaeInpExporter
from abqpilot.core.approval import APPROVAL_PHRASE, create_approval_token
from abqpilot.core.task_config import load_task_config, safety_flags
from abqpilot.core.task_result import make_task_result, write_json, write_result_json
from abqpilot.odb import OdbMetricsExtractor
from abqpilot.tools.diff_guard_tool import DiffGuard
from abqpilot.tools.odb_metrics_contract import write_odb_metrics_contract
from abqpilot.tools.physics_guard_tool import PhysicsGuard
from abqpilot.tools.real_sanity_base_intake import (
    MARKER_ID,
    detect_heat_input,
    write_manual_solver_handoff,
    write_marker_base,
    write_residual_stress_metrics_plan,
)
from abqpilot.tools.solver_output_intake import inventory_solver_outputs
from abqpilot.tools.solver_status_classifier import classify_solver_status
from abqpilot.tools.static_validator_tool import StaticValidator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK_CONFIG_PATH = PROJECT_ROOT / "configs" / "sanity_demo_task.json"
FINAL_STAGE2_VERDICT = "PASS_ABQPILOT_V2_STAGE2_0_CLI_SOFTWARE_ASSEMBLY_READY"


def command_status(config_path: str | Path | None = None, result_json: str | Path | None = None) -> dict[str, Any]:
    selected_config = config_path or (DEFAULT_TASK_CONFIG_PATH if DEFAULT_TASK_CONFIG_PATH.exists() else None)
    config = load_task_config(selected_config)
    details = {
        "project": "AbqPilot",
        "version": _version(),
        "cwd": str(Path.cwd()),
        "abaqus_command": config.get("abaqus_command"),
        "allow_cae_export": config.get("allow_cae_export"),
        "allow_odb_read": config.get("allow_odb_read"),
        "allow_solver_submit": False,
        "allow_abqjobpilot": False,
        "allow_abqjobpilot_preflight": False,
        "allow_abqjobpilot_dry_run_enqueue": False,
        "allow_jobpilot_enqueue_authorization": False,
        "allow_abqjobpilot_real_enqueue": False,
        "allow_llm": False,
        "verdict": "STATUS_OK",
    }
    result = make_task_result(
        command="status",
        verdict="STATUS_OK",
        success=True,
        safety_flags=safety_flags(config),
        details=details,
    )
    write_result_json(result, result_json)
    return result


def command_export_cae(
    cae: str | Path,
    out_dir: str | Path,
    job_name: str,
    config_path: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    config = load_task_config(config_path, {"allow_odb_read": False})
    exporter = CaeInpExporter(
        abaqus_command=str(config.get("abaqus_command")),
        allow_cae_export=bool(config.get("allow_cae_export")),
        cae_export_mode=str(config.get("cae_export_mode", "write_input_only")),
        allow_solver_submit=False,
        allow_odb_read=False,
        allow_abqjobpilot=False,
        allow_llm=False,
    )
    request = exporter.prepare_export(str(cae), str(out_dir), job_name)
    report = exporter.export(request)
    verdict = report["verdict"]
    result = make_task_result(
        command="export-cae",
        verdict=verdict,
        success=verdict in {"CAE_EXPORT_DISABLED", "CAE_EXPORT_COMPLETED"},
        output_paths={
            "expected_inp_path": report.get("expected_inp_path"),
            "request_json": str(Path(out_dir) / "cae_export_request.json"),
            "report_json": str(Path(out_dir) / "cae_export_report.json"),
        },
        safety_flags=safety_flags(config) | {"allow_odb_read": False},
        errors=report.get("errors", []),
        details={"request": request, "report": report},
    )
    write_result_json(result, result_json)
    return result


def command_audit_heat_x2(
    source_inp: str | Path,
    out_dir: str | Path,
    scale: float = 2.0,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    run_dir = Path(out_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    base_inp = run_dir / "base_heatflux_marker.inp"
    generated_inp = run_dir / "generated_power_x2.inp"

    intake_report = detect_heat_input(source_inp)
    write_json(run_dir / "intake_report.json", intake_report)
    if not intake_report.get("ok"):
        return _finish_audit_result(run_dir, source_inp, intake_report["verdict"], False, result_json, intake_report)

    marker_report = write_marker_base(source_inp, base_inp, intake_report)
    if not marker_report.get("ok"):
        return _finish_audit_result(
            run_dir,
            source_inp,
            "FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT",
            False,
            result_json,
            {"intake_report": intake_report, "marker_report": marker_report},
        )

    build_request = {
        "builder": "HeatFluxPatchBuilder",
        "heat_flux_scale": float(scale),
        "marker_id": MARKER_ID,
        "source_inp": str(base_inp),
        "output_inp": str(generated_inp),
        "base_inp_path": str(base_inp),
        "generated_inp_path": str(generated_inp),
        "parameters": {"heat_flux_scale": float(scale)},
    }
    write_json(run_dir / "build_request.json", build_request)
    build_status = HeatFluxPatchBuilder().build(build_request)
    write_json(run_dir / "build_status.json", build_status)
    if not build_status.get("allowed"):
        return _finish_audit_result(
            run_dir,
            source_inp,
            "FAIL_UNSUPPORTED_HEAT_INPUT_FORMAT",
            False,
            result_json,
            {"intake_report": intake_report, "marker_report": marker_report, "build_status": build_status},
        )

    validation_report = _validate_thermo_mechanical(generated_inp)
    write_json(run_dir / "validation_report.json", validation_report)
    if not validation_report.get("passed"):
        return _finish_audit_result(
            run_dir,
            source_inp,
            "FAIL_STATIC_VALIDATION",
            False,
            result_json,
            {
                "intake_report": intake_report,
                "marker_report": marker_report,
                "build_status": build_status,
                "validation_report": validation_report,
            },
        )

    diff_report = DiffGuard().compare(base_inp, generated_inp)
    write_json(run_dir / "diff_report.json", diff_report)
    physics_guard_report = PhysicsGuard().check(diff_report)
    write_json(run_dir / "physics_guard_report.json", physics_guard_report)
    if not physics_guard_report.get("passed"):
        return _finish_audit_result(
            run_dir,
            source_inp,
            "FAIL_PHYSICS_GUARD",
            False,
            result_json,
            {
                "intake_report": intake_report,
                "marker_report": marker_report,
                "build_status": build_status,
                "validation_report": validation_report,
                "diff_report": diff_report,
                "physics_guard_report": physics_guard_report,
            },
        )

    metrics_plan = write_residual_stress_metrics_plan(run_dir / "residual_stress_metrics_plan.json")
    manual_handoff = write_manual_solver_handoff(run_dir / "manual_solver_handoff.md", base_inp, generated_inp)
    selected = intake_report["selected_candidate"]
    details = {
        "source_inp": str(Path(source_inp)),
        "base_inp": str(base_inp),
        "generated_inp": str(generated_inp),
        "heat_input_keyword": selected["keyword"],
        "marker_id": MARKER_ID,
        "original_magnitude": build_status["original_magnitude"],
        "modified_magnitude": build_status["updated_magnitude"],
        "intake_report": intake_report,
        "marker_report": marker_report,
        "build_status": build_status,
        "validation_report": validation_report,
        "diff_report": diff_report,
        "physics_guard_report": physics_guard_report,
        "residual_stress_metrics_plan": metrics_plan,
        "manual_solver_handoff_preview_only": "PREVIEW_ONLY_NOT_EXECUTED" in manual_handoff,
    }
    return _finish_audit_result(
        run_dir,
        source_inp,
        "PASS_ABQPILOT_V2_STAGE2_0_HEAT_X2_AUDIT_READY",
        True,
        result_json,
        details,
    )


def command_intake_solver(
    search_root: str | Path,
    out_dir: str | Path,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    run_dir = Path(out_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    inventory = inventory_solver_outputs([search_root])
    write_json(run_dir / "solver_output_inventory.json", inventory)
    status_report = {
        "tool": "SolverStatusClassifier",
        "cases": [classify_solver_status(case) for case in inventory.get("cases", [])],
    }
    write_json(run_dir / "solver_status_report.json", status_report)
    verdict = _solver_intake_verdict(inventory, status_report)
    contract_path = run_dir / "odb_metrics_extraction_contract.json"
    if verdict not in {"FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND", "FAIL_ODB_PAIR_NOT_FOUND"}:
        write_odb_metrics_contract(contract_path, inventory["cases"])
    else:
        write_json(contract_path, {})

    details = {
        "search_root": str(Path(search_root)),
        "cases_detected": len(inventory.get("cases", [])),
        "inventory": inventory,
        "solver_status_report": status_report,
        "contract_path": str(contract_path),
    }
    result = make_task_result(
        command="intake-solver",
        verdict=verdict,
        success=verdict == "PASS_ABQPILOT_V2_STAGE2_0_SOLVER_INTAKE_READY",
        output_paths={
            "solver_output_inventory": str(run_dir / "solver_output_inventory.json"),
            "solver_status_report": str(run_dir / "solver_status_report.json"),
            "odb_metrics_extraction_contract": str(contract_path),
        },
        safety_flags=_stage2_safe_flags(),
        details=details,
    )
    write_result_json(result, result_json)
    return result


def command_extract_odb_metrics(
    contract: str | Path,
    out_dir: str | Path,
    config_path: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    config = load_task_config(config_path)
    extractor = OdbMetricsExtractor(
        abaqus_command=str(config.get("abaqus_command")),
        allow_odb_read=bool(config.get("allow_odb_read")),
        odb_read_mode=str(config.get("odb_read_mode")),
        allow_solver_submit=False,
        allow_abqjobpilot=False,
        allow_llm=False,
        timeout_s=600,
    )
    request = extractor.prepare_request(contract, out_dir)
    report = extractor.extract(request)
    result = make_task_result(
        command="extract-odb-metrics",
        verdict=report["verdict"],
        success=report["verdict"] == "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY",
        output_paths={
            "metrics_json": request.get("metrics_json_path"),
            "request_json": str(Path(out_dir) / "odb_metrics_extraction_request.json"),
            "report_json": str(Path(out_dir) / "odb_metrics_extraction_report.json"),
        },
        safety_flags=safety_flags(config) | {"allow_solver_submit": False, "allow_abqjobpilot": False, "allow_llm": False},
        errors=report.get("errors", []),
        details={"request": request, "report": report},
    )
    write_result_json(result, result_json)
    return result


def command_compare_metrics(
    metrics: str | Path,
    out_dir: str | Path,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    metrics_path = Path(metrics)
    run_dir = Path(out_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_pair = json.loads(metrics_path.read_text(encoding="utf-8"))
    comparison_report = build_comparison_report(metrics_pair, metrics_path)
    agent_observation = build_agent_observation(comparison_report)
    markdown = render_markdown_report(comparison_report)

    comparison_json = write_json(run_dir / "comparison_report.json", comparison_report)
    comparison_md = run_dir / "comparison_report.md"
    comparison_md.write_text(markdown, encoding="utf-8")
    observation_json = write_json(run_dir / "agent_observation.json", agent_observation)

    key_ratios = {
        "NT_max": comparison_report["metric_comparisons"].get("NT_max", {}).get("ratio"),
        "S_Mises_max": comparison_report["metric_comparisons"].get("S_Mises_max", {}).get("ratio"),
    }
    result = make_task_result(
        command="compare-metrics",
        verdict="PASS_ABQPILOT_V2_STAGE2_0_METRICS_COMPARISON_READY",
        success=True,
        output_paths={
            "comparison_report_json": comparison_json,
            "comparison_report_md": str(comparison_md),
            "agent_observation_json": observation_json,
        },
        safety_flags=_stage2_safe_flags(),
        details={
            "source_metrics_path": str(metrics_path),
            "key_ratios": key_ratios,
            "interpretation_summary": comparison_report["interpretation"]["summary"],
            "comparison_report": comparison_report,
            "agent_observation": agent_observation,
        },
    )
    write_result_json(result, result_json)
    return result


def command_run_sanity_demo(
    config_path: str | Path,
    mode: str = "through-comparison",
    task_id: str | None = None,
    work_root: str | Path | None = None,
    stop_after: str | None = None,
    resume: bool = False,
    force_step: str | None = None,
    skip_completed: bool = True,
    jobpilot_cpus: int | None = None,
    jobpilot_batch: str | None = None,
    jobpilot_strategy: str | None = None,
    abqjobpilot_root: str | Path | None = None,
    skip_jobpilot_preflight: bool = False,
    skip_jobpilot_dry_run_enqueue: bool = False,
    allow_real_jobpilot_enqueue: bool = False,
    skip_real_jobpilot_enqueue: bool = False,
    poll_jobpilot_status: bool = False,
    skip_jobpilot_status_poll: bool = False,
    jobpilot_job_id: str | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.core.pipeline_runner import PipelineRunner

    config_override = _load_config_for_runner(
        config_path,
        jobpilot_cpus=jobpilot_cpus,
        jobpilot_batch=jobpilot_batch,
        jobpilot_strategy=jobpilot_strategy,
        abqjobpilot_root=abqjobpilot_root,
        skip_jobpilot_preflight=skip_jobpilot_preflight,
        skip_jobpilot_dry_run_enqueue=skip_jobpilot_dry_run_enqueue,
        allow_real_jobpilot_enqueue=allow_real_jobpilot_enqueue,
        skip_real_jobpilot_enqueue=skip_real_jobpilot_enqueue,
        poll_jobpilot_status=poll_jobpilot_status,
        skip_jobpilot_status_poll=skip_jobpilot_status_poll,
        jobpilot_job_id=jobpilot_job_id,
    )

    if resume:
        if task_id is None:
            raise ValueError("--resume requires --task-id")
        runner = PipelineRunner.open_existing(
            config_path=config_path,
            task_id=task_id,
            work_root=work_root,
            skip_completed=skip_completed,
        )
        _apply_runner_config_override(runner, config_override)
        result = runner.resume()
        write_result_json(result, result_json)
        return result

    if force_step:
        if task_id is not None:
            if work_root is not None:
                task_root = Path(work_root)
            else:
                try:
                    task_root = Path(load_task_config(config_path)["work_root"])
                except FileNotFoundError:
                    task_root = Path("runs")
            task_dir = task_root / "tasks" / task_id
            if task_dir.exists():
                runner = PipelineRunner.open_existing(
                    config_path=config_path,
                    task_id=task_id,
                    work_root=work_root,
                    skip_completed=skip_completed,
                )
                _apply_runner_config_override(runner, config_override)
            else:
                runner = PipelineRunner(
                    config_path=config_path,
                    config=config_override,
                    task_id=task_id,
                    work_root=work_root,
                    skip_completed=skip_completed,
                )
        else:
            runner = PipelineRunner(
                config_path=config_path,
                config=config_override,
                task_id=task_id,
                work_root=work_root,
                skip_completed=skip_completed,
            )
        result = runner.run_step(force_step, force=True)
        if result["success"] and hasattr(runner, "workspace"):
            runner.workspace.stop_by_mode_limit()
        result = runner._finalize(result)
        write_result_json(result, result_json)
        return result

    runner = PipelineRunner(
        config_path=config_path,
        config=config_override,
        task_id=task_id,
        work_root=work_root,
        skip_completed=skip_completed,
    )
    selected_stop = stop_after or ("08_solver_intake" if mode == "prepare-only" else None)
    result = runner.run_until(selected_stop, mode_limit=(mode == "prepare-only")) if selected_stop else runner.run_all()
    write_result_json(result, result_json)
    return result


def command_approve_jobpilot_enqueue(
    task_dir: str | Path,
    approved_by: str,
    approval_phrase: str,
    expires_hours: int | float = 24,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    token_result = create_approval_token(
        task_dir=task_dir,
        approved_by=approved_by,
        approval_phrase=approval_phrase,
        expires_hours=expires_hours,
    )
    result = make_task_result(
        command="approve-jobpilot-enqueue",
        verdict=token_result["status"],
        success=bool(token_result.get("success")),
        output_paths={"approval_token_json": token_result.get("approval_token_path")},
        safety_flags=_stage2_safe_flags()
        | {
            "allow_jobpilot_enqueue_authorization": True,
            "allow_abqjobpilot_real_enqueue": False,
            "approval_phrase_required": APPROVAL_PHRASE,
        },
        errors=token_result.get("errors", []),
        warnings=token_result.get("warnings", []),
        details={"token_result": token_result, "task_dir": str(Path(task_dir))},
    )
    write_result_json(result, result_json)
    return result


def command_continue_from_job_output(
    task_dir: str | Path,
    manual_odb_path: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.core.completed_job_intake import continue_from_job_output

    result = continue_from_job_output(task_dir=task_dir, manual_odb_path=manual_odb_path)
    write_result_json(result, result_json)
    return result


def command_generate_repair_plan(
    task_dir: str | Path | None = None,
    metrics: str | Path | None = None,
    comparison: str | Path | None = None,
    out_dir: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.analysis.evaluation import evaluate_metrics
    from abqpilot.analysis.repair_plan import write_repair_plan

    task_path = Path(task_dir) if task_dir is not None else None
    metrics_path = Path(metrics) if metrics is not None else _artifact_path_from_task(task_path, "odb_metrics_json")
    comparison_path = Path(comparison) if comparison is not None else _artifact_path_from_task(task_path, "comparison_report_json")
    target_dir = Path(out_dir) if out_dir is not None else (task_path / "analysis" if task_path is not None else Path("runs") / "repair_plan")
    metrics_payload = _read_json_file(metrics_path) if metrics_path and metrics_path.exists() else {}
    comparison_payload = _read_json_file(comparison_path) if comparison_path and comparison_path.exists() else {}
    task_id = task_path.name if task_path is not None else None
    evaluation = evaluate_metrics(
        metrics=metrics_payload,
        comparison_report=comparison_payload,
        task_id=task_id,
        source_metrics=str(metrics_path) if metrics_path else None,
    )
    paths = write_repair_plan(target_dir, evaluation, task_id=task_id)
    if task_path is not None:
        _record_task_artifact(task_path, "evaluation_json", "generated", paths["evaluation_json"], "stage2_9_evaluation")
        _record_task_artifact(task_path, "repair_plan_json", "generated", paths["repair_plan_json"], "stage2_9_repair_plan")
        _record_task_artifact(task_path, "repair_plan_md", "generated", paths["repair_plan_md"], "stage2_9_repair_plan")
    result = make_task_result(
        command="generate-repair-plan",
        verdict=evaluation["evaluation_verdict"],
        success=evaluation["evaluation_verdict"] != "FAIL_STOP",
        output_paths=paths,
        safety_flags=_stage2_safe_flags(),
        warnings=[],
        errors=evaluation.get("errors", []),
        details={"evaluation": evaluation},
    )
    write_result_json(result, result_json)
    return result


def command_export_run_report(
    task_dir: str | Path,
    out_dir: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.reporting.run_report import export_run_report

    result = export_run_report(task_dir, out_dir=out_dir)
    write_result_json(result, result_json)
    return result


def command_alpha_freeze(
    root: str | Path = ".",
    test_results: str | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.reporting.alpha_freeze import export_alpha_freeze

    result = export_alpha_freeze(root=root, test_results=test_results)
    write_result_json(result, result_json)
    return result


def command_export_project_status(
    root: str | Path = ".",
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.reporting.project_status import export_project_status

    result = export_project_status(root=root)
    write_result_json(result, result_json)
    return result


def command_llm_reason(
    task_dir: str | Path | None = None,
    provider: str = "mock",
    model: str | None = None,
    confirm_send_task_summary: bool = False,
    dry_run_input_summary: bool = False,
    show_sanitized_summary: bool = False,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.llm.artifacts import write_reasoning_artifacts
    from abqpilot.llm.config import load_llm_config
    from abqpilot.llm.input_builder import build_sanitized_task_summary
    from abqpilot.llm.mock_reasoner import MockReasoner
    from abqpilot.llm.provider import OpenAICompatibleProvider

    config = load_llm_config(
        PROJECT_ROOT / ".env",
        {
            "ABQPILOT_LLM_PROVIDER": provider,
            "ABQPILOT_LLM_MODEL": model,
        },
    )
    summary = build_sanitized_task_summary(task_dir, config.max_input_chars) if task_dir else {}
    input_chars = len(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    request_metadata = {
        "provider": provider,
        "model": config.model,
        "llm_enabled": config.enabled,
        "sent_task_summary": False,
        "input_chars": input_chars,
        "task_summary_only": True,
        "authorization_header_written": False,
    }
    artifact_paths: dict[str, str] = {}

    if dry_run_input_summary:
        result = make_task_result(
            command="llm-reason",
            verdict="LLM_INPUT_SUMMARY_READY",
            success=True,
            output_paths={},
            safety_flags=_stage2_safe_flags() | {"sent_task_summary": False, "llm_provider": provider},
            details={
                "provider_config": config.masked(),
                "llm_enabled": config.enabled,
                "sent_task_summary": False,
                "input_chars": input_chars,
                "sanitized_summary": summary if show_sanitized_summary else None,
                "artifact_dir": None,
            },
        )
        write_result_json(result, result_json)
        return result

    if provider == "mock":
        reasoning = MockReasoner().reason(summary)
        if task_dir:
            artifact_paths = write_reasoning_artifacts(
                task_dir,
                summary,
                reasoning,
                {**request_metadata, "provider": "mock", "sent_task_summary": bool(task_dir)},
            )
        result = make_task_result(
            command="llm-reason",
            verdict=reasoning["verdict"],
            success=True,
            output_paths=artifact_paths,
            safety_flags=_stage2_safe_flags() | {"llm_provider": "mock", "sent_task_summary": bool(task_dir)},
            details={
                "provider_config": config.masked(),
                "reasoning": reasoning,
                "llm_enabled": config.enabled,
                "sent_task_summary": bool(task_dir),
                "input_chars": input_chars,
                "artifact_dir": artifact_paths.get("artifact_dir"),
                "sanitized_summary": summary if show_sanitized_summary else None,
            },
        )
        write_result_json(result, result_json)
        return result

    if not confirm_send_task_summary:
        result = make_task_result(
            command="llm-reason",
            verdict="LLM_TASK_SUMMARY_CONFIRMATION_REQUIRED",
            success=False,
            safety_flags=_stage2_safe_flags() | {"sent_task_summary": False},
            errors=["--confirm-send-task-summary is required for non-mock providers"],
            details={
                "provider_config": config.masked(),
                "llm_enabled": config.enabled,
                "sent_task_summary": False,
                "input_chars": input_chars,
                "artifact_dir": None,
                "sanitized_summary": summary if show_sanitized_summary else None,
            },
        )
        write_result_json(result, result_json)
        return result

    reasoning = OpenAICompatibleProvider(config).reason(summary)
    if task_dir:
        artifact_paths = write_reasoning_artifacts(
            task_dir,
            summary,
            reasoning,
            {**request_metadata, "sent_task_summary": True, "provider": config.provider},
        )
    validation = reasoning.get("validation", {})
    result = make_task_result(
        command="llm-reason",
        verdict=reasoning.get("verdict", "PROVIDER_ERROR"),
        success=reasoning.get("verdict") not in {"PROVIDER_ERROR", "LLM_OUTPUT_REJECTED_BY_SAFETY_VALIDATOR"}
        and validation.get("valid") is not False,
        output_paths=artifact_paths,
        safety_flags=_stage2_safe_flags() | {"sent_task_summary": True},
        details={
            "provider_config": config.masked(),
            "reasoning": reasoning,
            "llm_enabled": config.enabled,
            "sent_task_summary": True,
            "input_chars": input_chars,
            "artifact_dir": artifact_paths.get("artifact_dir"),
            "sanitized_summary": summary if show_sanitized_summary else None,
        },
        errors=[] if reasoning.get("verdict") != "PROVIDER_ERROR" else [reasoning.get("observation", "provider error")],
    )
    write_result_json(result, result_json)
    return result


def command_propose_patch(
    task_dir: str | Path,
    provider: str = "mock",
    model: str | None = None,
    confirm_send_patch_context: bool = False,
    dry_run_patch_context: bool = False,
    show_patch_context: bool = False,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.llm.config import load_llm_config
    from abqpilot.llm.patch_context_builder import build_patch_context
    from abqpilot.llm.patch_proposal_artifacts import write_patch_proposal_artifacts
    from abqpilot.llm.patch_proposal_reasoner import MockPatchProposalReasoner, OpenAICompatiblePatchProposalReasoner

    config = load_llm_config(
        PROJECT_ROOT / ".env",
        {
            "ABQPILOT_LLM_PROVIDER": provider,
            "ABQPILOT_LLM_MODEL": model,
        },
    )
    context = build_patch_context(task_dir, config.max_input_chars)
    input_chars = len(json.dumps(context, ensure_ascii=False, sort_keys=True))
    request_metadata = {
        "provider": provider,
        "model": config.model,
        "llm_enabled": config.enabled,
        "sent_patch_context": False,
        "input_chars": input_chars,
        "patch_context_only": True,
        "authorization_header_written": False,
    }
    if dry_run_patch_context:
        result = make_task_result(
            command="propose-patch",
            verdict="LLM_PATCH_CONTEXT_READY",
            success=True,
            safety_flags=_stage2_safe_flags() | {"sent_patch_context": False, "llm_provider": provider},
            details={
                "provider_config": config.masked(),
                "llm_enabled": config.enabled,
                "sent_patch_context": False,
                "input_chars": input_chars,
                "patch_context": context if show_patch_context else None,
                "artifact_dir": None,
            },
        )
        write_result_json(result, result_json)
        return result

    artifact_paths: dict[str, str] = {}
    if provider == "mock":
        proposal = MockPatchProposalReasoner().propose(context)
        artifact_paths = write_patch_proposal_artifacts(
            task_dir,
            context,
            proposal,
            {**request_metadata, "provider": "mock", "sent_patch_context": bool(task_dir)},
        )
        result = make_task_result(
            command="propose-patch",
            verdict=proposal["proposal_verdict"],
            success=proposal.get("validation", {}).get("valid") is True,
            output_paths=artifact_paths,
            safety_flags=_stage2_safe_flags() | {"llm_provider": "mock", "sent_patch_context": bool(task_dir)},
            details={
                "provider_config": config.masked(),
                "proposal": proposal,
                "llm_enabled": config.enabled,
                "sent_patch_context": bool(task_dir),
                "input_chars": input_chars,
                "artifact_dir": artifact_paths.get("artifact_dir"),
                "patch_context": context if show_patch_context else None,
            },
        )
        write_result_json(result, result_json)
        return result

    if not confirm_send_patch_context:
        result = make_task_result(
            command="propose-patch",
            verdict="LLM_PATCH_CONTEXT_CONFIRMATION_REQUIRED",
            success=False,
            safety_flags=_stage2_safe_flags() | {"sent_patch_context": False},
            errors=["--confirm-send-patch-context is required for non-mock providers"],
            details={
                "provider_config": config.masked(),
                "llm_enabled": config.enabled,
                "sent_patch_context": False,
                "input_chars": input_chars,
                "artifact_dir": None,
                "patch_context": context if show_patch_context else None,
            },
        )
        write_result_json(result, result_json)
        return result

    proposal = OpenAICompatiblePatchProposalReasoner(config).propose(context)
    artifact_paths = write_patch_proposal_artifacts(
        task_dir,
        context,
        proposal,
        {**request_metadata, "provider": config.provider, "sent_patch_context": True},
    )
    validation = proposal.get("validation", {})
    result = make_task_result(
        command="propose-patch",
        verdict=proposal.get("status") or proposal.get("proposal_verdict", "INSUFFICIENT_EVIDENCE"),
        success=validation.get("valid") is True and proposal.get("proposal_verdict") != "REJECTED_BY_SAFETY_VALIDATOR",
        output_paths=artifact_paths,
        safety_flags=_stage2_safe_flags() | {"sent_patch_context": True},
        details={
            "provider_config": config.masked(),
            "proposal": proposal,
            "llm_enabled": config.enabled,
            "sent_patch_context": True,
            "input_chars": input_chars,
            "artifact_dir": artifact_paths.get("artifact_dir"),
            "patch_context": context if show_patch_context else None,
        },
    )
    write_result_json(result, result_json)
    return result


def command_preview_patch(
    task_dir: str | Path,
    provider_source: str = "llm",
    proposal_path: str | Path | None = None,
    source_inp: str | Path | None = None,
    dry_run: bool = False,
    force_no_write: bool = False,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.patching.patch_preview import preview_patch

    result = preview_patch(
        task_dir=task_dir,
        proposal_path=proposal_path,
        source_inp=source_inp,
        dry_run=dry_run,
        force_no_write=force_no_write,
    )
    result["details"]["provider_source"] = provider_source
    result["safety_flags"] = _stage2_safe_flags() | {
        "solver_submitted": False,
        "job_enqueued": False,
        "queue_runner_launched": False,
        "opened_odb": False,
    }
    write_result_json(result, result_json)
    return result


def command_queue_patch_preview(
    task_dir: str | Path | None = None,
    patch_preview_dir: str | Path | None = None,
    candidate_inp: str | Path | None = None,
    mode: str = "preflight-only",
    workflow_dir: str | Path | None = None,
    approval_token: str | Path | None = None,
    abqjobpilot_root: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.patching.patch_queue_workflow import queue_patch_preview

    result = queue_patch_preview(
        task_dir=task_dir,
        patch_preview_dir=patch_preview_dir,
        candidate_inp=candidate_inp,
        mode=mode,
        workflow_dir=workflow_dir,
        approval_token=approval_token,
        abqjobpilot_root=abqjobpilot_root,
    )
    result["safety_flags"] = _stage2_safe_flags() | {
        "solver_submitted": False,
        "queue_runner_launched": False,
        "opened_odb": False,
        "llm_executed_action": False,
    }
    write_result_json(result, result_json)
    return result


def command_approve_patch_queue(
    workflow_dir: str | Path,
    approved_by: str,
    approval_phrase: str,
    expires_hours: int | float = 24,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.patching.patch_queue_workflow import PATCH_QUEUE_APPROVAL_PHRASE, approve_patch_queue

    token_result = approve_patch_queue(
        workflow_dir=workflow_dir,
        approved_by=approved_by,
        approval_phrase=approval_phrase,
        expires_hours=expires_hours,
    )
    result = make_task_result(
        command="approve-patch-queue",
        verdict=token_result["status"],
        success=bool(token_result.get("success")),
        output_paths={"approval_token_json": token_result.get("approval_token_path")},
        safety_flags=_stage2_safe_flags()
        | {
            "approval_phrase_required": PATCH_QUEUE_APPROVAL_PHRASE,
            "solver_submitted": False,
            "queue_runner_launched": False,
            "opened_odb": False,
        },
        details={"token_result": token_result, "workflow_dir": str(Path(workflow_dir))},
        errors=token_result.get("errors", []),
        warnings=token_result.get("warnings", []),
    )
    write_result_json(result, result_json)
    return result


def command_poll_patch_queue(
    workflow_dir: str | Path,
    abqjobpilot_root: str | Path | None = None,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.patching.patch_queue_workflow import poll_patch_queue

    result = poll_patch_queue(workflow_dir=workflow_dir, abqjobpilot_root=abqjobpilot_root)
    result["safety_flags"] = _stage2_safe_flags() | {
        "solver_submitted": False,
        "queue_runner_launched": False,
        "opened_odb": False,
    }
    write_result_json(result, result_json)
    return result


def command_probe_llm(
    provider: str = "chatanywhere",
    model: str | None = None,
    confirm_send_test_request: bool = False,
    result_json: str | Path | None = None,
) -> dict[str, Any]:
    from abqpilot.llm.config import load_llm_config
    from abqpilot.llm.provider import OpenAICompatibleProvider

    config = load_llm_config(
        PROJECT_ROOT / ".env",
        {
            "ABQPILOT_LLM_PROVIDER": provider,
            "ABQPILOT_LLM_MODEL": model,
        },
    )
    if not confirm_send_test_request:
        result = make_task_result(
            command="probe-llm",
            verdict="LLM_PROBE_CONFIRMATION_REQUIRED",
            success=False,
            safety_flags=_stage2_safe_flags() | {"sent_test_request": False},
            errors=["--confirm-send-test-request is required before any real provider probe"],
            details={"provider_config": config.masked()},
        )
        write_result_json(result, result_json)
        return result
    probe = OpenAICompatibleProvider(config).probe()
    result = make_task_result(
        command="probe-llm",
        verdict=probe.get("verdict", "PROVIDER_ERROR"),
        success=probe.get("verdict") != "PROVIDER_ERROR",
        safety_flags=_stage2_safe_flags() | {"sent_test_request": True, "sent_task_summary": False},
        details={"provider_config": config.masked(), "probe": probe},
        errors=[] if probe.get("verdict") != "PROVIDER_ERROR" else [probe.get("summary", "provider error")],
    )
    write_result_json(result, result_json)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abqpilot", description="AbqPilot deterministic CLI task runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Show deterministic runtime safety status")
    status.add_argument("--config", default=None)
    status.add_argument("--result-json", default=None)

    export = subparsers.add_parser("export-cae", help="Prepare or run gated CAE writeInput export")
    export.add_argument("--cae", required=True)
    export.add_argument("--out-dir", required=True)
    export.add_argument("--job-name", required=True)
    export.add_argument("--config", default=None)
    export.add_argument("--result-json", default=None)

    audit = subparsers.add_parser("audit-heat-x2", help="Audit deterministic heat input scale patch")
    audit.add_argument("--source-inp", required=True)
    audit.add_argument("--out-dir", required=True)
    audit.add_argument("--scale", type=float, default=2.0)
    audit.add_argument("--result-json", default=None)

    intake = subparsers.add_parser("intake-solver", help="Inspect existing manual solver outputs")
    intake.add_argument("--search-root", required=True)
    intake.add_argument("--out-dir", required=True)
    intake.add_argument("--result-json", default=None)

    extract = subparsers.add_parser("extract-odb-metrics", help="Run gated metrics-only ODB extractor")
    extract.add_argument("--contract", required=True)
    extract.add_argument("--out-dir", required=True)
    extract.add_argument("--config", default=None)
    extract.add_argument("--result-json", default=None)

    compare = subparsers.add_parser("compare-metrics", help="Compare existing metrics JSON")
    compare.add_argument("--metrics", required=True)
    compare.add_argument("--out-dir", required=True)
    compare.add_argument("--result-json", default=None)

    demo = subparsers.add_parser("run-sanity-demo", help="Run deterministic sanity demo task runner")
    demo.add_argument("--config", required=True)
    demo.add_argument("--mode", choices=["prepare-only", "through-comparison"], default="through-comparison")
    demo.add_argument("--task-id", default=None)
    demo.add_argument("--work-root", default=None)
    demo.add_argument("--stop-after", default=None)
    demo.add_argument("--resume", action="store_true")
    demo.add_argument("--force-step", default=None)
    demo.add_argument("--skip-completed", dest="skip_completed", action="store_true", default=True)
    demo.add_argument("--no-skip-completed", dest="skip_completed", action="store_false")
    demo.add_argument("--jobpilot-cpus", type=int, default=14)
    demo.add_argument("--jobpilot-batch", default="sanity_base_heat_x2")
    demo.add_argument("--jobpilot-strategy", default="power_x2")
    demo.add_argument("--abqjobpilot-root", default=None)
    demo.add_argument("--skip-jobpilot-preflight", action="store_true")
    demo.add_argument("--skip-jobpilot-dry-run-enqueue", action="store_true")
    demo.add_argument("--allow-real-jobpilot-enqueue", action="store_true")
    demo.add_argument("--skip-real-jobpilot-enqueue", action="store_true")
    demo.add_argument("--poll-jobpilot-status", action="store_true")
    demo.add_argument("--skip-jobpilot-status-poll", action="store_true")
    demo.add_argument("--jobpilot-job-id", default=None)
    demo.add_argument("--result-json", default=None)

    approve = subparsers.add_parser("approve-jobpilot-enqueue", help="Create a manual approval token for a future enqueue stage")
    approve.add_argument("--task-dir", required=True)
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--approval-phrase", required=True)
    approve.add_argument("--expires-hours", type=float, default=24)
    approve.add_argument("--result-json", default=None)

    continue_parser = subparsers.add_parser("continue-from-job-output", help="Validate existing job output evidence for continuation")
    continue_parser.add_argument("--task-dir", required=True)
    continue_parser.add_argument("--manual-odb-path", default=None)
    continue_parser.add_argument("--result-json", default=None)

    repair = subparsers.add_parser("generate-repair-plan", help="Generate deterministic evaluation and repair-plan artifacts")
    repair.add_argument("--task-dir", default=None)
    repair.add_argument("--metrics", default=None)
    repair.add_argument("--comparison", default=None)
    repair.add_argument("--out-dir", default=None)
    repair.add_argument("--result-json", default=None)

    report = subparsers.add_parser("export-run-report", help="Export a Markdown/JSON report for a task workspace")
    report.add_argument("--task-dir", required=True)
    report.add_argument("--out-dir", default=None)
    report.add_argument("--result-json", default=None)

    freeze = subparsers.add_parser("alpha-freeze", help="Export an alpha freeze report package")
    freeze.add_argument("--root", default=".")
    freeze.add_argument("--test-results", default=None)
    freeze.add_argument("--result-json", default=None)

    project_status = subparsers.add_parser("export-project-status", help="Export current project status files")
    project_status.add_argument("--root", default=str(PROJECT_ROOT))
    project_status.add_argument("--result-json", default=None)

    llm_reason = subparsers.add_parser("llm-reason", help="Run optional bounded LLM reasoner contract")
    llm_reason.add_argument("--task-dir", default=None)
    llm_reason.add_argument("--provider", default="mock")
    llm_reason.add_argument("--model", default=None)
    llm_reason.add_argument("--confirm-send-task-summary", action="store_true")
    llm_reason.add_argument("--dry-run-input-summary", action="store_true")
    llm_reason.add_argument("--show-sanitized-summary", action="store_true")
    llm_reason.add_argument("--result-json", default=None)

    propose_patch = subparsers.add_parser("propose-patch", help="Generate advisory LLM candidate patch proposal")
    propose_patch.add_argument("--task-dir", required=True)
    propose_patch.add_argument("--provider", default="mock")
    propose_patch.add_argument("--model", default=None)
    propose_patch.add_argument("--confirm-send-patch-context", action="store_true")
    propose_patch.add_argument("--dry-run-patch-context", action="store_true")
    propose_patch.add_argument("--show-patch-context", action="store_true")
    propose_patch.add_argument("--result-json", default=None)

    preview_patch_parser = subparsers.add_parser("preview-patch", help="Create guarded deterministic candidate INP preview from a patch proposal")
    preview_patch_parser.add_argument("--task-dir", required=True)
    preview_patch_parser.add_argument("--provider-source", default="llm")
    preview_patch_parser.add_argument("--proposal-path", default=None)
    preview_patch_parser.add_argument("--source-inp", default=None)
    preview_patch_parser.add_argument("--dry-run", action="store_true")
    preview_patch_parser.add_argument("--force-no-write", action="store_true")
    preview_patch_parser.add_argument("--result-json", default=None)

    queue_patch = subparsers.add_parser("queue-patch-preview", help="Run guarded patch candidate JobPilot queue workflow")
    queue_patch.add_argument("--task-dir", default=None)
    queue_patch.add_argument("--patch-preview-dir", default=None)
    queue_patch.add_argument("--candidate-inp", default=None)
    queue_patch.add_argument("--workflow-dir", default=None)
    queue_patch.add_argument("--mode", choices=["preflight-only", "dry-run-enqueue", "real-queue-only"], default="preflight-only")
    queue_patch.add_argument("--approval-token", default=None)
    queue_patch.add_argument("--abqjobpilot-root", default=None)
    queue_patch.add_argument("--result-json", default=None)

    approve_patch_queue = subparsers.add_parser("approve-patch-queue", help="Create approval token for a patch candidate queue-only enqueue")
    approve_patch_queue.add_argument("--workflow-dir", required=True)
    approve_patch_queue.add_argument("--approved-by", required=True)
    approve_patch_queue.add_argument("--approval-phrase", required=True)
    approve_patch_queue.add_argument("--expires-hours", type=float, default=24)
    approve_patch_queue.add_argument("--result-json", default=None)

    poll_patch_queue = subparsers.add_parser("poll-patch-queue", help="Read-only status poll for a patch candidate queue workflow")
    poll_patch_queue.add_argument("--workflow-dir", required=True)
    poll_patch_queue.add_argument("--abqjobpilot-root", default=None)
    poll_patch_queue.add_argument("--result-json", default=None)

    probe_llm = subparsers.add_parser("probe-llm", help="Probe configured OpenAI-compatible LLM provider")
    probe_llm.add_argument("--provider", default="chatanywhere")
    probe_llm.add_argument("--model", default=None)
    probe_llm.add_argument("--confirm-send-test-request", action="store_true")
    probe_llm.add_argument("--result-json", default=None)

    subparsers.add_parser("gui", help="Launch the local GUI beta")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "status":
        result = command_status(args.config, args.result_json)
    elif args.command == "export-cae":
        result = command_export_cae(args.cae, args.out_dir, args.job_name, args.config, args.result_json)
    elif args.command == "audit-heat-x2":
        result = command_audit_heat_x2(args.source_inp, args.out_dir, args.scale, args.result_json)
    elif args.command == "intake-solver":
        result = command_intake_solver(args.search_root, args.out_dir, args.result_json)
    elif args.command == "extract-odb-metrics":
        result = command_extract_odb_metrics(args.contract, args.out_dir, args.config, args.result_json)
    elif args.command == "compare-metrics":
        result = command_compare_metrics(args.metrics, args.out_dir, args.result_json)
    elif args.command == "run-sanity-demo":
        result = command_run_sanity_demo(
            args.config,
            args.mode,
            task_id=args.task_id,
            work_root=args.work_root,
            stop_after=args.stop_after,
            resume=args.resume,
            force_step=args.force_step,
            skip_completed=args.skip_completed,
            jobpilot_cpus=args.jobpilot_cpus,
            jobpilot_batch=args.jobpilot_batch,
            jobpilot_strategy=args.jobpilot_strategy,
            abqjobpilot_root=args.abqjobpilot_root,
            skip_jobpilot_preflight=args.skip_jobpilot_preflight,
            skip_jobpilot_dry_run_enqueue=args.skip_jobpilot_dry_run_enqueue,
            allow_real_jobpilot_enqueue=args.allow_real_jobpilot_enqueue,
            skip_real_jobpilot_enqueue=args.skip_real_jobpilot_enqueue,
            poll_jobpilot_status=args.poll_jobpilot_status,
            skip_jobpilot_status_poll=args.skip_jobpilot_status_poll,
            jobpilot_job_id=args.jobpilot_job_id,
            result_json=args.result_json,
        )
    elif args.command == "approve-jobpilot-enqueue":
        result = command_approve_jobpilot_enqueue(
            task_dir=args.task_dir,
            approved_by=args.approved_by,
            approval_phrase=args.approval_phrase,
            expires_hours=args.expires_hours,
            result_json=args.result_json,
        )
    elif args.command == "continue-from-job-output":
        result = command_continue_from_job_output(
            task_dir=args.task_dir,
            manual_odb_path=args.manual_odb_path,
            result_json=args.result_json,
        )
    elif args.command == "generate-repair-plan":
        result = command_generate_repair_plan(
            task_dir=args.task_dir,
            metrics=args.metrics,
            comparison=args.comparison,
            out_dir=args.out_dir,
            result_json=args.result_json,
        )
    elif args.command == "export-run-report":
        result = command_export_run_report(args.task_dir, out_dir=args.out_dir, result_json=args.result_json)
    elif args.command == "alpha-freeze":
        result = command_alpha_freeze(root=args.root, test_results=args.test_results, result_json=args.result_json)
    elif args.command == "export-project-status":
        result = command_export_project_status(root=args.root, result_json=args.result_json)
    elif args.command == "llm-reason":
        result = command_llm_reason(
            task_dir=args.task_dir,
            provider=args.provider,
            model=args.model,
            confirm_send_task_summary=args.confirm_send_task_summary,
            dry_run_input_summary=args.dry_run_input_summary,
            show_sanitized_summary=args.show_sanitized_summary,
            result_json=args.result_json,
        )
    elif args.command == "propose-patch":
        result = command_propose_patch(
            task_dir=args.task_dir,
            provider=args.provider,
            model=args.model,
            confirm_send_patch_context=args.confirm_send_patch_context,
            dry_run_patch_context=args.dry_run_patch_context,
            show_patch_context=args.show_patch_context,
            result_json=args.result_json,
        )
    elif args.command == "preview-patch":
        result = command_preview_patch(
            task_dir=args.task_dir,
            provider_source=args.provider_source,
            proposal_path=args.proposal_path,
            source_inp=args.source_inp,
            dry_run=args.dry_run,
            force_no_write=args.force_no_write,
            result_json=args.result_json,
        )
    elif args.command == "queue-patch-preview":
        result = command_queue_patch_preview(
            task_dir=args.task_dir,
            patch_preview_dir=args.patch_preview_dir,
            candidate_inp=args.candidate_inp,
            workflow_dir=args.workflow_dir,
            mode=args.mode,
            approval_token=args.approval_token,
            abqjobpilot_root=args.abqjobpilot_root,
            result_json=args.result_json,
        )
    elif args.command == "approve-patch-queue":
        result = command_approve_patch_queue(
            workflow_dir=args.workflow_dir,
            approved_by=args.approved_by,
            approval_phrase=args.approval_phrase,
            expires_hours=args.expires_hours,
            result_json=args.result_json,
        )
    elif args.command == "poll-patch-queue":
        result = command_poll_patch_queue(
            workflow_dir=args.workflow_dir,
            abqjobpilot_root=args.abqjobpilot_root,
            result_json=args.result_json,
        )
    elif args.command == "probe-llm":
        result = command_probe_llm(
            provider=args.provider,
            model=args.model,
            confirm_send_test_request=args.confirm_send_test_request,
            result_json=args.result_json,
        )
    elif args.command == "gui":
        from abqpilot.gui.app import main as gui_main

        gui_main()
        return 0
    else:
        parser.error(f"unknown command: {args.command}")

    _print_result(result)
    return 0 if result["success"] or result["verdict"] in _CONTROLLED_STOP_VERDICTS else 1


def _print_result(result: dict[str, Any]) -> None:
    command = result["command"]
    details = result.get("details", {})
    print(f"command={command}")
    print(f"verdict={result['verdict']}")
    if command == "status":
        for key in (
            "project",
            "version",
            "cwd",
            "abaqus_command",
            "allow_cae_export",
            "allow_odb_read",
            "allow_solver_submit",
            "allow_abqjobpilot",
            "allow_llm",
        ):
            print(f"{key}={details.get(key)}")
    elif command == "export-cae":
        print(f"expected_inp_path={result['output_paths'].get('expected_inp_path')}")
    elif command == "audit-heat-x2":
        print(f"heat_input_keyword={details.get('heat_input_keyword')}")
        print(f"original_magnitude={details.get('original_magnitude')}")
        print(f"modified_magnitude={details.get('modified_magnitude')}")
    elif command == "intake-solver":
        print(f"cases_detected={details.get('cases_detected')}")
        statuses = {item["case_id"]: item["status"] for item in details.get("solver_status_report", {}).get("cases", [])}
        for case in details.get("inventory", {}).get("cases", []):
            print(
                f"case={case['case_id']} role={case['expected_role']} "
                f"odb_exists={str(case['odb_exists']).lower()} "
                f"lock_exists={str(case['lock_exists']).lower()} "
                f"status={statuses.get(case['case_id'], 'UNKNOWN')}"
            )
    elif command == "extract-odb-metrics":
        print(f"metrics_json_path={result['output_paths'].get('metrics_json')}")
    elif command == "compare-metrics":
        ratios = details.get("key_ratios", {})
        print(f"NT_max_ratio={ratios.get('NT_max')}")
        print(f"S_Mises_max_ratio={ratios.get('S_Mises_max')}")
        for item in details.get("interpretation_summary", []):
            print(f"interpretation={item}")
    elif command == "run-sanity-demo":
        print(f"task_id={result.get('task_id')}")
        print(f"task_dir={result.get('task_dir')}")
        print(f"final_status={result.get('final_status')}")
        print(f"current_step={result.get('current_step')}")
        print(f"stop_reason={result.get('stop_reason')}")
        print(f"requires_human_action={str(result.get('requires_human_action')).lower()}")
        print(f"human_action_reason={result.get('human_action_reason')}")
        print(f"abqjobpilot_project_root={result.get('abqjobpilot_project_root')}")
        print(f"abqjobpilot_available={result.get('abqjobpilot_available')}")
        print(f"abqjobpilot_preflight_status={result.get('abqjobpilot_preflight_status')}")
        print(f"abqjobpilot_command_preview_path={result.get('abqjobpilot_command_preview_path')}")
        print(f"abqjobpilot_dry_run_enqueue_status={result.get('abqjobpilot_dry_run_enqueue_status')}")
        print(f"abqjobpilot_dry_run_result_path={result.get('abqjobpilot_dry_run_result_path')}")
        print(f"abqjobpilot_runtime_mutation_detected={result.get('abqjobpilot_runtime_mutation_detected')}")
        print(f"jobpilot_enqueue_authorization_status={result.get('jobpilot_enqueue_authorization_status')}")
        print(f"jobpilot_enqueue_approval_request_path={result.get('jobpilot_enqueue_approval_request_path')}")
        print(f"jobpilot_enqueue_approval_token_path={result.get('jobpilot_enqueue_approval_token_path')}")
        print(f"abqjobpilot_real_enqueue_status={result.get('abqjobpilot_real_enqueue_status')}")
        print(f"abqjobpilot_real_enqueue_result_path={result.get('abqjobpilot_real_enqueue_result_path')}")
        print(f"abqjobpilot_real_enqueue_queue_mutated={result.get('abqjobpilot_real_enqueue_queue_mutated')}")
        print(
            "abqjobpilot_real_enqueue_forbidden_mutation_detected="
            f"{result.get('abqjobpilot_real_enqueue_forbidden_mutation_detected')}"
        )
        print(f"abqjobpilot_job_id={result.get('abqjobpilot_job_id')}")
        print(f"abqjobpilot_raw_status={result.get('abqjobpilot_raw_status')}")
        print(f"abqjobpilot_normalized_status={result.get('abqjobpilot_normalized_status')}")
        print(f"abqjobpilot_expected_odb_path={result.get('abqjobpilot_expected_odb_path')}")
        print(f"abqjobpilot_odb_exists={result.get('abqjobpilot_odb_exists')}")
        print(f"abqjobpilot_lock_exists={result.get('abqjobpilot_lock_exists')}")
        print(f"abqjobpilot_status_summary_path={result.get('abqjobpilot_status_summary_path')}")
        print(f"task_state_json={result['output_paths'].get('task_state_json')}")
    elif command == "approve-jobpilot-enqueue":
        print(f"approval_token_path={result['output_paths'].get('approval_token_json')}")
        print(f"token_status={result['verdict']}")
    elif command == "continue-from-job-output":
        details = result.get("details", {})
        print(f"task_id={details.get('task_id')}")
        print(f"job_id={details.get('job_id')}")
        print(f"normalized_status={details.get('normalized_status')}")
        print(f"accepted_odb_path={details.get('accepted_odb_path')}")
        print(f"odb_exists={details.get('odb_exists')}")
        print(f"lock_exists={details.get('lock_exists')}")
        print(f"continue_to_solver_intake={details.get('continue_to_solver_intake')}")
        print(f"summary_json={result['output_paths'].get('stage2_8_completed_job_intake_summary_json')}")
    elif command == "generate-repair-plan":
        print(f"evaluation_json={result['output_paths'].get('evaluation_json')}")
        print(f"repair_plan_json={result['output_paths'].get('repair_plan_json')}")
        print(f"repair_plan_md={result['output_paths'].get('repair_plan_md')}")
    elif command == "export-run-report":
        print(f"run_report_json={result['output_paths'].get('run_report_json')}")
        print(f"run_report_md={result['output_paths'].get('run_report_md')}")
    elif command == "alpha-freeze":
        print(f"alpha_freeze_dir={result['output_paths'].get('alpha_freeze_dir')}")
        print(f"alpha_freeze_report_json={result['output_paths'].get('alpha_freeze_report_json')}")
    elif command == "export-project-status":
        print(f"project_status_json={result['output_paths'].get('project_status_json')}")
        print(f"project_status_md={result['output_paths'].get('project_status_md')}")
    elif command in {"llm-reason", "probe-llm"}:
        config = details.get("provider_config", {})
        reasoning = details.get("reasoning") or details.get("probe") or {}
        print(f"provider={config.get('provider')}")
        print(f"model={config.get('model')}")
        print(f"llm_enabled={details.get('llm_enabled', config.get('enabled'))}")
        if command == "probe-llm":
            print(f"api_key={config.get('api_key')}")
        print(f"sent_task_summary={details.get('sent_task_summary')}")
        print(f"input_chars={details.get('input_chars')}")
        print(f"llm_verdict={reasoning.get('verdict')}")
        print(f"recommended_next_action={reasoning.get('recommended_next_action')}")
        print(f"human_review_required={reasoning.get('human_review_required')}")
        print(f"safety_validator={reasoning.get('validation', {}).get('status')}")
        print(f"artifact_dir={details.get('artifact_dir')}")
        if details.get("sanitized_summary") is not None:
            print("sanitized_summary=" + json.dumps(details["sanitized_summary"], ensure_ascii=False, sort_keys=True))
    elif command == "propose-patch":
        config = details.get("provider_config", {})
        proposal = details.get("proposal", {})
        candidate = proposal.get("candidate_patch", {})
        print(f"provider={config.get('provider')}")
        print(f"model={config.get('model')}")
        print(f"llm_enabled={details.get('llm_enabled', config.get('enabled'))}")
        print(f"sent_patch_context={details.get('sent_patch_context')}")
        print(f"input_chars={details.get('input_chars')}")
        print(f"proposal_verdict={proposal.get('proposal_verdict')}")
        print(f"patch_type={candidate.get('patch_type')}")
        print(f"requires_human_review={candidate.get('requires_human_review')}")
        print(f"safety_validator={proposal.get('validation', {}).get('status')}")
        print(f"artifact_dir={details.get('artifact_dir')}")
        if details.get("patch_context") is not None:
            print("patch_context=" + json.dumps(details["patch_context"], ensure_ascii=False, sort_keys=True))
    elif command == "preview-patch":
        print(f"preview_status={details.get('preview_status')}")
        print(f"patch_type={details.get('patch_type')}")
        print(f"source_inp_path={details.get('source_inp_path')}")
        print(f"candidate_inp_path={details.get('candidate_inp_path')}")
        print(f"static_validator_status={details.get('static_validator_status')}")
        print(f"diff_guard_status={details.get('diff_guard_status')}")
        print(f"physics_guard_status={details.get('physics_guard_status')}")
        print(f"changed_lines_count={details.get('changed_lines_count')}")
        print(f"unrelated_changes_count={details.get('unrelated_changes_count')}")
        print(f"solver_submitted={details.get('solver_submitted')}")
        print(f"job_enqueued={details.get('job_enqueued')}")
        print(f"artifact_dir={result.get('output_paths', {}).get('artifact_dir')}")
    elif command == "queue-patch-preview":
        print(f"workflow_status={details.get('workflow_status')}")
        print(f"patch_type={details.get('patch_type')}")
        print(f"candidate_inp_path={details.get('candidate_inp_path')}")
        print(f"candidate_inp_sha256={details.get('candidate_inp_sha256')}")
        print(f"preflight_status={details.get('preflight_status')}")
        print(f"dry_run_enqueue_status={details.get('dry_run_enqueue_status')}")
        print(f"approval_status={details.get('approval_status')}")
        print(f"real_enqueue_status={details.get('real_enqueue_status')}")
        print(f"job_id={details.get('job_id')}")
        print(f"queue_only={details.get('queue_only')}")
        print(f"queue_file_mutated={details.get('queue_file_mutated')}")
        print(f"solver_started={details.get('solver_started')}")
        print(f"runner_started={details.get('runner_started')}")
        print(f"gui_required={details.get('gui_required')}")
        print(f"forbidden_mutations_detected={details.get('forbidden_mutations_detected')}")
        print(f"normalized_status={details.get('normalized_status')}")
        print(f"final_pipeline_status={details.get('final_pipeline_status')}")
        print(f"artifact_dir={result.get('output_paths', {}).get('artifact_dir')}")
        print(f"solver_submitted={details.get('solver_submitted')}")
        print(f"queue_runner_launched={details.get('queue_runner_launched')}")
        print(f"opened_odb={details.get('opened_odb')}")
    elif command == "approve-patch-queue":
        print(f"approval_token_path={result['output_paths'].get('approval_token_json')}")
        print(f"token_status={result['verdict']}")
    elif command == "poll-patch-queue":
        print(f"job_id={details.get('job_id')}")
        print(f"raw_status={details.get('raw_status')}")
        print(f"normalized_status={details.get('normalized_status')}")
        print(f"expected_odb_path={details.get('expected_odb_path')}")
        print(f"odb_exists={details.get('odb_exists')}")
        print(f"lock_exists={details.get('lock_exists')}")
        print(f"artifact_dir={result.get('output_paths', {}).get('artifact_dir')}")
        print(f"solver_submitted={details.get('solver_submitted')}")
        print(f"queue_runner_launched={details.get('queue_runner_launched')}")
        print(f"opened_odb={details.get('opened_odb')}")


def _finish_audit_result(
    run_dir: Path,
    source_inp: str | Path,
    verdict: str,
    success: bool,
    result_json: str | Path | None,
    details: dict[str, Any],
) -> dict[str, Any]:
    output_paths = {
        "base_heatflux_marker": str(run_dir / "base_heatflux_marker.inp"),
        "generated_power_x2": str(run_dir / "generated_power_x2.inp"),
        "intake_report": str(run_dir / "intake_report.json"),
        "build_status": str(run_dir / "build_status.json"),
        "validation_report": str(run_dir / "validation_report.json"),
        "diff_report": str(run_dir / "diff_report.json"),
        "physics_guard_report": str(run_dir / "physics_guard_report.json"),
    }
    if "source_inp" not in details:
        details = {"source_inp": str(Path(source_inp)), **details}
    result = make_task_result(
        command="audit-heat-x2",
        verdict=verdict,
        success=success,
        output_paths=output_paths,
        safety_flags=_stage2_safe_flags(),
        details=details,
    )
    write_json(run_dir / "final_verdict.json", {"verdict": verdict, **details})
    write_result_json(result, result_json)
    return result


def _validate_thermo_mechanical(inp_path: Path) -> dict[str, Any]:
    text = inp_path.read_text(encoding="utf-8", errors="replace")
    temperature_token = "NT11" if "nt11" in text.lower() else "NT" if _has_output_token(text, "NT") else None
    stress_present = _has_output_token(text, "S")
    required_tokens = ["*Heading", "*Step", "*End Step", "*Output", temperature_token or "NT11_OR_NT", "S"]
    report = StaticValidator().validate(inp_path, target_region=None, required_tokens=required_tokens)
    if not stress_present and "S" not in report["missing"]:
        report["missing"].append("S")
    if temperature_token is None and "NT11_OR_NT" not in report["missing"]:
        report["missing"].append("NT11_OR_NT")
    report["NT11_literal_present"] = "nt11" in text.lower()
    report["temperature_output_token"] = temperature_token
    report["target_region_status"] = "TARGET_REGION_NOT_CONFIRMED"
    report["passed"] = not report["missing"] and not report["errors"]
    return report


def _has_output_token(text: str, token: str) -> bool:
    target = token.lower()
    for line in text.splitlines():
        if line.lstrip().startswith("*") or line.lstrip().startswith("**"):
            continue
        tokens = [part.strip().lower() for part in line.split(",")]
        if target in tokens:
            return True
    return False


def _solver_intake_verdict(inventory: dict[str, Any], status_report: dict[str, Any]) -> str:
    cases = inventory.get("cases", [])
    if len(cases) != 2:
        return "FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND"
    if not all(case.get("odb_exists") for case in cases):
        return "FAIL_ODB_PAIR_NOT_FOUND"
    if any(item["status"] == "FAILED" for item in status_report.get("cases", [])):
        return "FAIL_SOLVER_OUTPUT_FAILED"
    return "PASS_ABQPILOT_V2_STAGE2_0_SOLVER_INTAKE_READY"


def _stage2_safe_flags() -> dict[str, Any]:
    return {
        "allow_cae_export": False,
        "allow_odb_read": False,
        "odb_read_mode": "disabled",
        "allow_solver_submit": False,
        "allow_abqjobpilot": False,
        "allow_abqjobpilot_preflight": False,
        "allow_abqjobpilot_dry_run_enqueue": False,
        "allow_jobpilot_enqueue_authorization": False,
        "allow_abqjobpilot_real_enqueue": False,
        "allow_abqjobpilot_status_poll": False,
        "allow_llm": False,
        "allow_cae_modify": False,
    }


_CONTROLLED_STOP_VERDICTS = {
    "STOPPED_BY_MODE_LIMIT",
    "NEED_EXPORTED_INP",
    "NEED_MANUAL_SOLVER_OUTPUTS",
    "NEED_ODB_METRICS_JSON",
    "NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT",
    "NEED_JOBPILOT_PREFLIGHT_REQUEST",
    "NEED_JOBPILOT_AUTHORIZATION_EVIDENCE",
    "NEED_ABQJOBPILOT_JOB_ID",
}


def _load_config_for_runner(
    config_path: str | Path,
    jobpilot_cpus: int | None,
    jobpilot_batch: str | None,
    jobpilot_strategy: str | None,
    abqjobpilot_root: str | Path | None,
    skip_jobpilot_preflight: bool,
    skip_jobpilot_dry_run_enqueue: bool,
    allow_real_jobpilot_enqueue: bool,
    skip_real_jobpilot_enqueue: bool,
    poll_jobpilot_status: bool,
    skip_jobpilot_status_poll: bool,
    jobpilot_job_id: str | None,
) -> dict[str, Any] | None:
    try:
        config = load_task_config(config_path)
    except FileNotFoundError:
        return None
    jobpilot = dict(config.get("jobpilot", {}))
    if jobpilot_cpus is not None:
        jobpilot["cpus"] = int(jobpilot_cpus)
    if jobpilot_batch is not None:
        jobpilot["batch"] = jobpilot_batch
    if jobpilot_strategy is not None:
        jobpilot["strategy"] = jobpilot_strategy
    jobpilot["submission_mode"] = "preview_only"
    jobpilot["allow_solver_submit"] = False
    config["jobpilot"] = jobpilot
    abqjobpilot = dict(config.get("abqjobpilot", {}))
    if abqjobpilot_root is not None:
        abqjobpilot["project_root"] = str(abqjobpilot_root)
    if jobpilot_cpus is not None:
        abqjobpilot["cpus"] = int(jobpilot_cpus)
    if jobpilot_batch is not None:
        abqjobpilot["batch"] = jobpilot_batch
    if jobpilot_strategy is not None:
        abqjobpilot["strategy"] = jobpilot_strategy
    abqjobpilot["submission_mode"] = "preview_only"
    abqjobpilot["allow_solver_submit"] = False
    abqjobpilot.setdefault("dry_run_enqueue_enabled", True)
    abqjobpilot.setdefault("real_enqueue_enabled", bool(allow_real_jobpilot_enqueue))
    abqjobpilot.setdefault("real_enqueue_mode", "queue_only")
    abqjobpilot.setdefault("require_approval_token", True)
    abqjobpilot.setdefault("status_poll_enabled", True)
    abqjobpilot.setdefault("status_poll_read_only", True)
    config["abqjobpilot"] = abqjobpilot
    if allow_real_jobpilot_enqueue:
        config["allow_abqjobpilot_real_enqueue"] = True
        abqjobpilot["real_enqueue_enabled"] = True
    else:
        config["allow_abqjobpilot_real_enqueue"] = bool(config.get("allow_abqjobpilot_real_enqueue", False))
    if skip_jobpilot_preflight:
        config["skip_jobpilot_preflight"] = True
    if skip_jobpilot_dry_run_enqueue:
        config["skip_jobpilot_dry_run_enqueue"] = True
    if skip_real_jobpilot_enqueue:
        config["skip_real_jobpilot_enqueue"] = True
    if poll_jobpilot_status:
        config["poll_jobpilot_status"] = True
        config["allow_abqjobpilot_status_poll"] = True
    else:
        config["allow_abqjobpilot_status_poll"] = bool(config.get("allow_abqjobpilot_status_poll", False))
    if skip_jobpilot_status_poll:
        config["skip_jobpilot_status_poll"] = True
    if jobpilot_job_id:
        config["jobpilot_job_id"] = jobpilot_job_id
        config["poll_jobpilot_status"] = True
        config["allow_abqjobpilot_status_poll"] = True
    return config


def _apply_runner_config_override(runner: Any, config_override: dict[str, Any] | None) -> None:
    if config_override is None or not hasattr(runner, "workspace"):
        return
    runner.config.update(config_override)
    runner.workspace.config = dict(runner.config)
    runner.workspace.save_config()


def _artifact_path_from_task(task_dir: Path | None, artifact_name: str) -> Path | None:
    if task_dir is None:
        return None
    artifacts_path = task_dir / "artifacts.json"
    if not artifacts_path.exists():
        return None
    try:
        payload = json.loads(artifacts_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for artifact in payload.get("artifacts", []):
        if artifact.get("name") == artifact_name and artifact.get("path"):
            return Path(artifact["path"])
    return None


def _read_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _record_task_artifact(task_dir: Path, name: str, kind: str, path: str | Path, producer_step: str) -> None:
    artifacts_path = task_dir / "artifacts.json"
    payload = {"task_id": task_dir.name, "artifacts": []}
    if artifacts_path.exists():
        try:
            payload = json.loads(artifacts_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    artifact = {
        "name": name,
        "kind": kind,
        "path": str(path),
        "exists": Path(path).exists(),
        "producer_step": producer_step,
    }
    for existing in payload.setdefault("artifacts", []):
        if existing.get("name") == name:
            existing.update(artifact)
            break
    else:
        payload["artifacts"].append(artifact)
    artifacts_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _version() -> str:
    try:
        return metadata.version("abqpilot")
    except metadata.PackageNotFoundError:
        return "0.1.0"


if __name__ == "__main__":
    raise SystemExit(main())
