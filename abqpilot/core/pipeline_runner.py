from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from abqpilot.core.pipeline_steps import STEP_NAMES, run_pipeline_step
from abqpilot.core.task_config import load_task_config, safety_flags
from abqpilot.core.task_result import make_task_result
from abqpilot.core.task_workspace import TaskWorkspace, _now


FINAL_PASS = "PASS_ABQPILOT_V2_STAGE2_6_CONTROLLED_REAL_QUEUE_ENQUEUE_GATE_READY"
STOP_REASONS = {
    "STOPPED_BY_MODE_LIMIT",
    "NEED_EXPORTED_INP",
    "NEED_MANUAL_SOLVER_OUTPUTS",
    "NEED_ODB_METRICS_JSON",
    "NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT",
    "NEED_JOBPILOT_PREFLIGHT_REQUEST",
    "NEED_JOBPILOT_AUTHORIZATION_EVIDENCE",
    "NEED_ABQJOBPILOT_JOB_ID",
    "STEP_FAILED",
    "PIPELINE_COMPLETED",
}


class PipelineRunner:
    def __init__(
        self,
        config_path: str | Path | None = None,
        config: dict[str, Any] | None = None,
        task_id: str | None = None,
        work_root: str | Path | None = None,
        skip_completed: bool = True,
        load_existing: bool = False,
    ) -> None:
        self.config_path = Path(config_path) if config_path is not None else None
        self.config = dict(config) if config is not None else load_task_config(config_path)
        if work_root is not None:
            self.config["work_root"] = str(work_root)
        self.skip_completed = skip_completed
        if load_existing:
            if task_id is None:
                raise ValueError("task_id is required when loading an existing task")
            self.workspace = TaskWorkspace.load_existing(
                config=self.config,
                work_root=self.config["work_root"],
                task_id=task_id,
                step_names=STEP_NAMES,
            )
            self.config = self.workspace.config
        else:
            self.workspace = TaskWorkspace(
                self.config,
                work_root=self.config["work_root"],
                task_id=task_id,
                step_names=STEP_NAMES,
            ).create()
        self.config_path_for_steps = self.workspace.config_path
        self.trace: list[dict[str, Any]] = self.workspace.load_trace()

    @classmethod
    def open_existing(
        cls,
        config_path: str | Path,
        task_id: str,
        work_root: str | Path | None = None,
        skip_completed: bool = True,
    ) -> "PipelineRunner":
        return cls(
            config_path=config_path,
            task_id=task_id,
            work_root=work_root,
            skip_completed=skip_completed,
            load_existing=True,
        )

    def run_all(self) -> dict[str, Any]:
        return self.run_until(STEP_NAMES[-1])

    def run_until(self, step_name: str, mode_limit: bool = False) -> dict[str, Any]:
        if step_name not in STEP_NAMES:
            raise ValueError(f"unknown pipeline step: {step_name}")
        final: dict[str, Any] | None = None
        for candidate in STEP_NAMES[: STEP_NAMES.index(step_name) + 1]:
            final = self.run_step(candidate)
            if final["verdict"] in {
                "NEED_EXPORTED_INP",
                "NEED_MANUAL_SOLVER_OUTPUTS",
                "NEED_ODB_METRICS_JSON",
                "NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT",
                "NEED_JOBPILOT_PREFLIGHT_REQUEST",
                "NEED_JOBPILOT_AUTHORIZATION_EVIDENCE",
                "NEED_ABQJOBPILOT_JOB_ID",
            }:
                return self._finalize(final)
            if candidate == "07_abqjobpilot_status_poll" and final["verdict"] in {
                "JOB_QUEUED",
                "JOB_RUNNING",
                "JOB_OUTPUTS_READY",
                "JOB_ODB_MISSING",
                "JOB_FAILED",
                "JOB_LOCKED",
                "JOB_UNKNOWN",
                "ABQJOBPILOT_UNAVAILABLE",
            }:
                self._stop_for_jobpilot_status(final["verdict"])
                self._append_trace(
                    "PIPELINE_STOPPED",
                    candidate,
                    final["verdict"],
                    self.workspace.state.get("stop_reason"),
                    final.get("result_path"),
                )
                return self._finalize(final)
            if final["verdict"] == "REAL_ENQUEUE_COMPLETED":
                self.workspace.stop_for_abqjobpilot_or_manual_solver()
                self._append_trace(
                    "PIPELINE_STOPPED",
                    candidate,
                    final["verdict"],
                    "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER",
                    final.get("result_path"),
                )
                return self._finalize(final)
            if not final["success"] and final["verdict"] != "SKIPPED_EXISTING_COMPLETED_STEP":
                self.workspace.stop_failed("STEP_FAILED")
                self._append_trace("PIPELINE_STOPPED", candidate, final["verdict"], "STEP_FAILED", final.get("result_path"))
                return self._finalize(final)
        if final and step_name == STEP_NAMES[-1] and final["success"]:
            self.workspace.stop_completed()
            final["verdict"] = FINAL_PASS
            self._append_trace("PIPELINE_STOPPED", step_name, final["verdict"], "PIPELINE_COMPLETED", None)
        elif final and final["success"] and mode_limit:
            self.workspace.stop_by_mode_limit()
            final = self._mode_limit_result(step_name)
            self._append_trace("PIPELINE_STOPPED", step_name, final["verdict"], "STOPPED_BY_MODE_LIMIT", None)
        return self._finalize(final or self._base_final("STOPPED_BY_MODE_LIMIT", False))

    def resume(self) -> dict[str, Any]:
        self._append_trace("PIPELINE_RESUMED", self.workspace.state.get("current_step"), None, "resume requested", None)
        start = self._first_non_completed_step()
        if start is None:
            self.workspace.stop_completed()
            return self._finalize(self._base_final(FINAL_PASS, True))
        return self.run_until(STEP_NAMES[-1])

    def run_step(self, step_name: str, force: bool = False) -> dict[str, Any]:
        if step_name not in STEP_NAMES:
            raise ValueError(f"unknown pipeline step: {step_name}")

        step_state = self.workspace.step_state(step_name)
        result_path = self.workspace.step_result_path(step_name)
        if _should_recheck_authorization_step(self.workspace, step_name, step_state):
            force = True
        if not force and not self.skip_completed and step_state.get("status") == "COMPLETED" and result_path.exists():
            force = True
        if not force and self.skip_completed and step_state.get("status") == "COMPLETED" and result_path.exists():
            result = make_task_result(
                command=step_name,
                verdict="SKIPPED_EXISTING_COMPLETED_STEP",
                success=True,
                output_paths={"step_result_json": str(result_path)},
                safety_flags=self.workspace.state["safety_flags"],
                details={"original_result_path": str(result_path)},
            )
            self.workspace.mark_step_skipped(step_name, result["verdict"])
            self._append_trace("STEP_SKIPPED", step_name, result["verdict"], "completed step result exists", result_path)
            return result

        if force and self.workspace.step_dir(step_name).exists() and any(self.workspace.step_dir(step_name).iterdir()):
            backup_path = self._backup_step_dir(step_name)
            self.workspace.registry.add_artifact(
                f"{step_name}_rerun_backup_{self.workspace.step_state(step_name)['rerun_count'] + 1:03d}",
                "backup",
                backup_path,
                step_name,
            )
            self.workspace.save_artifacts()
            self.workspace.increment_rerun_count(step_name)
            self._append_trace("STEP_STARTED", step_name, None, f"force rerun backup created: {backup_path}", None)
        else:
            self._append_trace("STEP_STARTED", step_name, None, "step started", None)

        self.workspace.mark_step_running(step_name)
        context = self._context(step_name)
        result = run_pipeline_step(step_name, context)
        self._record_artifacts(step_name, result)
        self._write_step_result(step_name, result)

        if result["success"]:
            self.workspace.mark_step_completed(step_name, result["verdict"], result_path)
            self._append_trace("STEP_COMPLETED", step_name, result["verdict"], None, result_path)
        else:
            if result["verdict"] == "NEED_MANUAL_SOLVER_OUTPUTS":
                self.workspace.mark_step_waiting(step_name, result["verdict"], result_path)
                self.workspace.stop_for_manual_solver()
                self._append_trace("PIPELINE_STOPPED", step_name, result["verdict"], "NEED_MANUAL_SOLVER_OUTPUTS", result_path)
            elif result["verdict"] in {
                "NEED_EXPORTED_INP",
                "NEED_ODB_METRICS_JSON",
                "NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT",
                "NEED_JOBPILOT_PREFLIGHT_REQUEST",
                "NEED_JOBPILOT_AUTHORIZATION_EVIDENCE",
                "NEED_ABQJOBPILOT_JOB_ID",
            }:
                self.workspace.mark_step_failed(step_name, result["verdict"], result_path)
                self.workspace.stop_failed(result["verdict"])
                self._append_trace("STEP_FAILED", step_name, result["verdict"], result["verdict"], result_path)
            else:
                self.workspace.mark_step_failed(step_name, result["verdict"], result_path)
                self._append_trace("STEP_FAILED", step_name, result["verdict"], "STEP_FAILED", result_path)
        return result

    def _context(self, step_name: str) -> dict[str, Any]:
        return {
            "step_name": step_name,
            "step_dir": self.workspace.step_dir(step_name),
            "task_dir": self.workspace.task_dir,
            "config": self.config,
            "config_path": self.config_path_for_steps,
            "safety_flags": safety_flags(self.config) | {
                "allow_solver_submit": False,
                "allow_abqjobpilot": False,
                "allow_llm": False,
                "allow_codex_runtime": False,
            },
            "exported_inp_path": _artifact_path(self.workspace, "exported_inp"),
            "candidate_inp_path": _artifact_path(self.workspace, "generated_power_x2"),
            "abqjobpilot_request_path": _artifact_path(self.workspace, "abqjobpilot_job_request"),
            "abqjobpilot_preflight_result_path": _artifact_path(self.workspace, "abqjobpilot_preflight_result"),
            "abqjobpilot_dry_run_result_path": _artifact_path(self.workspace, "abqjobpilot_dry_run_enqueue_result"),
            "abqjobpilot_real_enqueue_result_path": _artifact_path(self.workspace, "abqjobpilot_real_enqueue_result"),
            "odb_contract_path": _artifact_path(self.workspace, "odb_metrics_contract"),
            "metrics_json_path": _artifact_path(self.workspace, "odb_metrics_json"),
            "jobpilot_enqueue_authorization_report_path": _artifact_path(
                self.workspace, "jobpilot_enqueue_authorization_report_json"
            ),
            "task_id": self.workspace.task_id,
        }

    def _record_artifacts(self, step_name: str, result: dict[str, Any]) -> None:
        output_paths = result.get("output_paths", {})
        if step_name == "01_export_cae":
            expected = output_paths.get("expected_inp_path")
            if expected:
                self.workspace.registry.add_artifact("exported_inp", "generated", expected, step_name)
            for key in ("request_json", "report_json"):
                if output_paths.get(key):
                    self.workspace.registry.add_artifact(key, "generated", output_paths[key], step_name)
        elif step_name == "02_audit_heat_x2":
            for name in ("base_heatflux_marker", "generated_power_x2"):
                if output_paths.get(name):
                    self.workspace.registry.add_artifact(name, "generated", output_paths[name], step_name)
        elif step_name == "03_abqjobpilot_preflight":
            for name in (
                "abqjobpilot_job_request",
                "abqjobpilot_preflight_result",
                "abqjobpilot_command_preview",
            ):
                if output_paths.get(name):
                    self.workspace.registry.add_artifact(name, "generated", output_paths[name], step_name)
        elif step_name == "04_abqjobpilot_dry_run_enqueue":
            for name in (
                "abqjobpilot_dry_run_request",
                "abqjobpilot_dry_run_enqueue_result",
                "abqjobpilot_dry_run_safety_report",
                "abqjobpilot_dry_run_preview",
            ):
                if output_paths.get(name):
                    self.workspace.registry.add_artifact(name, "generated", output_paths[name], step_name)
        elif step_name == "05_jobpilot_enqueue_authorization":
            for name in (
                "jobpilot_enqueue_approval_request",
                "jobpilot_enqueue_authorization_report_json",
                "jobpilot_enqueue_authorization_report_md",
                "jobpilot_enqueue_approval_token",
            ):
                if output_paths.get(name):
                    self.workspace.registry.add_artifact(name, "generated", output_paths[name], step_name)
        elif step_name == "06_abqjobpilot_real_enqueue":
            for name in (
                "abqjobpilot_real_enqueue_request",
                "abqjobpilot_real_enqueue_result",
                "abqjobpilot_real_enqueue_safety_report",
                "abqjobpilot_real_enqueue_preview",
            ):
                if output_paths.get(name):
                    self.workspace.registry.add_artifact(name, "generated", output_paths[name], step_name)
        elif step_name == "07_abqjobpilot_status_poll":
            for name in (
                "abqjobpilot_status_request",
                "abqjobpilot_status_result",
                "abqjobpilot_output_locator_result",
                "abqjobpilot_status_summary",
                "abqjobpilot_status_summary_md",
            ):
                if output_paths.get(name):
                    self.workspace.registry.add_artifact(name, "generated", output_paths[name], step_name)
            summary_path = output_paths.get("abqjobpilot_status_summary")
            expected_odb = _expected_odb_from_status_summary(summary_path)
            if expected_odb:
                self.workspace.registry.add_artifact("expected_odb", "referenced", expected_odb, step_name)
        elif step_name == "08_solver_intake":
            if output_paths.get("odb_metrics_extraction_contract"):
                self.workspace.registry.add_artifact(
                    "odb_metrics_contract",
                    "generated",
                    output_paths["odb_metrics_extraction_contract"],
                    step_name,
                )
        elif step_name == "09_odb_metrics":
            if output_paths.get("metrics_json"):
                self.workspace.registry.add_artifact("odb_metrics_json", "generated", output_paths["metrics_json"], step_name)
        elif step_name == "10_compare_metrics":
            for key, path in output_paths.items():
                self.workspace.registry.add_artifact(key, "generated", path, step_name)
        self.workspace.save_artifacts()

    def _write_step_result(self, step_name: str, result: dict[str, Any]) -> None:
        path = self.workspace.step_result_path(step_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    def _backup_step_dir(self, step_name: str) -> Path:
        step_dir = self.workspace.step_dir(step_name)
        next_index = int(self.workspace.step_state(step_name).get("rerun_count", 0)) + 1
        backup_dir = self.workspace.steps_dir / f"{step_name}__rerun_backup_{next_index:03d}"
        while backup_dir.exists():
            next_index += 1
            backup_dir = self.workspace.steps_dir / f"{step_name}__rerun_backup_{next_index:03d}"
        shutil.copytree(step_dir, backup_dir)
        return backup_dir

    def _append_trace(
        self,
        event: str,
        step: str | None,
        verdict: str | None,
        reason: str | None,
        result_path: str | Path | None,
    ) -> None:
        entry = {
            "timestamp": _now(),
            "event": event,
            "step": step,
            "verdict": verdict,
            "reason": reason,
            "result_path": str(result_path) if result_path is not None else None,
        }
        self.trace.append(entry)
        self.workspace.save_trace(self.trace)

    def _first_non_completed_step(self) -> str | None:
        for step_name in STEP_NAMES:
            step = self.workspace.step_state(step_name)
            if step.get("status") != "COMPLETED" or not self.workspace.step_result_path(step_name).exists():
                return step_name
        return None

    def _mode_limit_result(self, step_name: str) -> dict[str, Any]:
        return make_task_result(
            command="run-sanity-demo",
            verdict="STOPPED_BY_MODE_LIMIT",
            success=True,
            safety_flags=self.workspace.state["safety_flags"],
            details={"stopped_after": step_name},
        )

    def _finalize(self, result: dict[str, Any]) -> dict[str, Any]:
        final = {
            "command": "run-sanity-demo",
            "verdict": result["verdict"],
            "success": bool(result.get("success")),
            "task_id": self.workspace.task_id,
            "task_dir": str(self.workspace.task_dir),
            "final_status": self.workspace.state["status"],
            "current_step": self.workspace.state["current_step"],
            "stop_reason": self.workspace.state.get("stop_reason"),
            "requires_human_action": self.workspace.state["requires_human_action"],
            "human_action_reason": self.workspace.state["human_action_reason"],
            "abqjobpilot_project_root": _preflight_field(self.workspace, "project_root"),
            "abqjobpilot_available": _preflight_field(self.workspace, "available"),
            "abqjobpilot_preflight_status": _artifact_status(self.workspace, "abqjobpilot_preflight_result"),
            "abqjobpilot_command_preview_path": _artifact_path(self.workspace, "abqjobpilot_command_preview"),
            "abqjobpilot_dry_run_enqueue_status": _artifact_status(self.workspace, "abqjobpilot_dry_run_enqueue_result"),
            "abqjobpilot_dry_run_result_path": _artifact_path(self.workspace, "abqjobpilot_dry_run_enqueue_result"),
            "abqjobpilot_runtime_mutation_detected": _dry_run_field(self.workspace, "runtime_mutation_detected"),
            "jobpilot_enqueue_authorization_status": _artifact_status(
                self.workspace, "jobpilot_enqueue_authorization_report_json"
            ),
            "jobpilot_enqueue_approval_request_path": _artifact_path(self.workspace, "jobpilot_enqueue_approval_request"),
            "jobpilot_enqueue_approval_token_path": _artifact_path(self.workspace, "jobpilot_enqueue_approval_token")
            or _approval_token_path_if_exists(self.workspace),
            "abqjobpilot_real_enqueue_status": _artifact_status(self.workspace, "abqjobpilot_real_enqueue_result"),
            "abqjobpilot_real_enqueue_result_path": _artifact_path(self.workspace, "abqjobpilot_real_enqueue_result"),
            "abqjobpilot_real_enqueue_queue_mutated": _real_enqueue_field(self.workspace, "queue_mutated"),
            "abqjobpilot_real_enqueue_forbidden_mutation_detected": _real_enqueue_field(
                self.workspace, "forbidden_mutation_detected"
            ),
            "abqjobpilot_job_id": _status_summary_field(self.workspace, "job_id")
            or _real_enqueue_field(self.workspace, "job_id"),
            "abqjobpilot_raw_status": _status_summary_field(self.workspace, "raw_status"),
            "abqjobpilot_normalized_status": _status_summary_field(self.workspace, "normalized_status"),
            "abqjobpilot_expected_odb_path": _status_summary_field(self.workspace, "expected_odb_path"),
            "abqjobpilot_odb_exists": _status_summary_field(self.workspace, "odb_exists"),
            "abqjobpilot_lock_exists": _status_summary_field(self.workspace, "lock_exists"),
            "abqjobpilot_status_summary_path": _artifact_path(self.workspace, "abqjobpilot_status_summary"),
            "output_paths": {
                "task_state_json": str(self.workspace.state_path),
                "artifacts_json": str(self.workspace.artifacts_path),
                "pipeline_trace_json": str(self.workspace.trace_path),
                "final_result_json": str(self.workspace.final_result_path),
            },
            "safety_flags": self.workspace.state["safety_flags"],
            "warnings": result.get("warnings", []),
            "errors": result.get("errors", []),
            "details": {
                "step_result": result,
                "task_state": self.workspace.state,
                "artifacts": self.workspace.registry.to_dict(),
            },
        }
        self.workspace.save_final_result(final)
        return final

    def _stop_for_jobpilot_status(self, normalized_status: str) -> None:
        if normalized_status in {"JOB_QUEUED", "JOB_RUNNING"}:
            self.workspace.state["status"] = "WAITING_FOR_ABQJOBPILOT"
            self.workspace.state["stop_reason"] = "WAITING_FOR_ABQJOBPILOT"
            self.workspace.state["requires_human_action"] = False
            self.workspace.state["human_action_reason"] = None
        elif normalized_status == "JOB_OUTPUTS_READY":
            self.workspace.state["status"] = "JOB_OUTPUTS_READY"
            self.workspace.state["stop_reason"] = "JOB_OUTPUTS_READY"
            self.workspace.state["requires_human_action"] = False
            self.workspace.state["human_action_reason"] = None
        elif normalized_status == "JOB_ODB_MISSING":
            self.workspace.state["status"] = "JOB_ODB_MISSING"
            self.workspace.state["stop_reason"] = "JOB_ODB_MISSING"
            self.workspace.state["requires_human_action"] = False
            self.workspace.state["human_action_reason"] = None
        elif normalized_status == "JOB_FAILED":
            self.workspace.state["status"] = "JOB_FAILED"
            self.workspace.state["stop_reason"] = "JOB_FAILED"
            self.workspace.state["requires_human_action"] = False
            self.workspace.state["human_action_reason"] = None
        else:
            self.workspace.state["status"] = normalized_status
            self.workspace.state["stop_reason"] = normalized_status
            self.workspace.state["requires_human_action"] = False
            self.workspace.state["human_action_reason"] = None
        self.workspace.save_state()

    @staticmethod
    def _base_final(verdict: str, success: bool) -> dict[str, Any]:
        return {"command": "pipeline", "verdict": verdict, "success": success, "output_paths": {}, "details": {}}


def _artifact_path(workspace: TaskWorkspace, name: str) -> str | None:
    artifact = workspace.registry.get_artifact(name)
    if not artifact:
        return None
    return artifact.get("path")


def _artifact_status(workspace: TaskWorkspace, name: str) -> str | None:
    path = _artifact_path(workspace, name)
    if not path or not Path(path).exists():
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get("status")


def _preflight_field(workspace: TaskWorkspace, field_name: str) -> Any | None:
    path = _artifact_path(workspace, "abqjobpilot_preflight_result")
    if not path or not Path(path).exists():
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get(field_name)


def _dry_run_field(workspace: TaskWorkspace, field_name: str) -> Any | None:
    path = _artifact_path(workspace, "abqjobpilot_dry_run_enqueue_result")
    if not path or not Path(path).exists():
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get(field_name)


def _real_enqueue_field(workspace: TaskWorkspace, field_name: str) -> Any | None:
    path = _artifact_path(workspace, "abqjobpilot_real_enqueue_result")
    if not path or not Path(path).exists():
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get(field_name)


def _status_summary_field(workspace: TaskWorkspace, field_name: str) -> Any | None:
    path = _artifact_path(workspace, "abqjobpilot_status_summary")
    if not path or not Path(path).exists():
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get(field_name)


def _expected_odb_from_status_summary(path: str | Path | None) -> str | None:
    if not path or not Path(path).exists():
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload.get("expected_odb_path")


def _approval_token_path_if_exists(workspace: TaskWorkspace) -> str | None:
    path = workspace.task_dir / "approvals" / "jobpilot_enqueue_approval_token.json"
    return str(path) if path.exists() else None


def _should_recheck_authorization_step(workspace: TaskWorkspace, step_name: str, step_state: dict[str, Any]) -> bool:
    if step_name != "05_jobpilot_enqueue_authorization":
        return False
    if step_state.get("status") != "COMPLETED" or step_state.get("verdict") != "APPROVAL_REQUIRED":
        return False
    return (workspace.task_dir / "approvals" / "jobpilot_enqueue_approval_token.json").exists()
