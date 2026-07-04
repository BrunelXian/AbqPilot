from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from abqpilot import cli
from abqpilot.gui.artifact_viewer import preview_artifact
from abqpilot.gui.task_loader import discover_recent_tasks, load_task_summary
from abqpilot.gui.workflow_presets import workflow_presets
from abqpilot.ui_state.view_model import build_task_view_model


BLOCKED_VERDICT = "ACTION_BLOCKED_BY_SAFETY_BOUNDARY"


class GuiActionController:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)

    def load_task(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("load_task", lambda: self._load_task(task_dir))

    def refresh_task(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("refresh_task", lambda: self._load_task(task_dir, refreshed=True))

    def recent_tasks(self, work_root: str | Path | None = None, limit: int = 10) -> dict[str, Any]:
        root = Path(work_root) if work_root is not None else self.project_root / "runs"
        return self._safe(
            "recent_tasks",
            lambda: {
                "command": "recent_tasks",
                "verdict": "RECENT_TASKS_READY",
                "success": True,
                "tasks": discover_recent_tasks(root, limit=limit),
                "errors": [],
                "warnings": [],
            },
        )

    def run_prepare_pipeline(
        self,
        config_path: str | Path,
        task_id: str | None,
        abqjobpilot_root: str | Path | None = None,
    ) -> dict[str, Any]:
        return self._safe(
            "run_prepare_pipeline",
            lambda: cli.command_run_sanity_demo(
                config_path=config_path,
                mode="prepare-only",
                task_id=task_id,
                abqjobpilot_root=abqjobpilot_root,
            ),
        )

    def create_approval_token(
        self,
        task_dir: str | Path,
        approved_by: str,
        approval_phrase: str,
        expires_hours: int = 24,
    ) -> dict[str, Any]:
        return self._safe(
            "create_approval_token",
            lambda: cli.command_approve_jobpilot_enqueue(
                task_dir=task_dir,
                approved_by=approved_by,
                approval_phrase=approval_phrase,
                expires_hours=expires_hours,
            ),
        )

    def poll_jobpilot_status(self, task_dir: str | Path, abqjobpilot_root: str | Path | None = None) -> dict[str, Any]:
        def action() -> dict[str, Any]:
            task = Path(task_dir)
            return cli.command_run_sanity_demo(
                task / "task_config.json",
                task_id=task.name,
                resume=True,
                abqjobpilot_root=abqjobpilot_root,
                poll_jobpilot_status=True,
            )

        return self._safe("poll_jobpilot_status", action)

    def continue_from_job_output(self, task_dir: str | Path, manual_odb_path: str | Path | None = None) -> dict[str, Any]:
        return self._safe(
            "continue_from_job_output",
            lambda: cli.command_continue_from_job_output(task_dir=task_dir, manual_odb_path=manual_odb_path),
        )

    def generate_repair_plan(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("generate_repair_plan", lambda: cli.command_generate_repair_plan(task_dir=task_dir))

    def export_run_report(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("export_run_report", lambda: cli.command_export_run_report(task_dir=task_dir))

    def preview_llm_input_summary(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "preview_llm_input_summary",
            lambda: cli.command_llm_reason(
                task_dir=task_dir,
                provider="mock",
                dry_run_input_summary=True,
                show_sanitized_summary=True,
            ),
        )

    def run_mock_reasoner(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("run_mock_reasoner", lambda: cli.command_llm_reason(task_dir=task_dir, provider="mock"))

    def run_real_llm_reasoner(
        self,
        task_dir: str | Path,
        provider: str = "chatanywhere",
        model: str | None = None,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        if not confirmed:
            return {
                "command": "run_real_llm_reasoner",
                "verdict": "GUI_LLM_CONFIRMATION_REQUIRED",
                "success": False,
                "errors": ["Real LLM reasoning requires explicit confirmation before sending a sanitized task summary."],
                "warnings": [],
            }
        return self._safe(
            "run_real_llm_reasoner",
            lambda: cli.command_llm_reason(
                task_dir=task_dir,
                provider=provider,
                model=model,
                confirm_send_task_summary=True,
            ),
        )

    def preview_patch_context(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "preview_patch_context",
            lambda: cli.command_propose_patch(
                task_dir=task_dir,
                provider="mock",
                dry_run_patch_context=True,
                show_patch_context=True,
            ),
        )

    def propose_patch_mock(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("propose_patch_mock", lambda: cli.command_propose_patch(task_dir=task_dir, provider="mock"))

    def propose_patch_real(
        self,
        task_dir: str | Path,
        provider: str = "chatanywhere",
        model: str | None = None,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        if not confirmed:
            return {
                "command": "propose_patch_real",
                "verdict": "GUI_PATCH_CONTEXT_CONFIRMATION_REQUIRED",
                "success": False,
                "errors": ["Real LLM patch proposal requires explicit confirmation before sending sanitized patch context."],
                "warnings": [],
            }
        return self._safe(
            "propose_patch_real",
            lambda: cli.command_propose_patch(
                task_dir=task_dir,
                provider=provider,
                model=model,
                confirm_send_patch_context=True,
            ),
        )

    def preview_guarded_patch(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe("preview_guarded_patch", lambda: cli.command_preview_patch(task_dir=task_dir, provider_source="llm"))

    def preview_dflux_deactivation_patch(
        self,
        source_inp: str | Path,
        output_dir: str | Path | None = None,
        compare_successful_job_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        return self._safe(
            "preview_dflux_deactivation_patch",
            lambda: cli.command_preview_dflux_deactivation_patch(
                source_inp=source_inp,
                output_dir=output_dir,
                compare_successful_job_dir=compare_successful_job_dir,
            ),
        )

    def run_model_condition_guard(
        self,
        source_jnl: str | Path,
        source_inp: str | Path,
        candidate_inp: str | Path,
        solver_inp: str | Path | None = None,
        output_dir: str | Path | None = None,
        target_change: str | None = None,
    ) -> dict[str, Any]:
        from abqpilot.cli import command_run_model_condition_guard

        return self._safe(
            "run_model_condition_guard",
            lambda: command_run_model_condition_guard(
                source_jnl=source_jnl,
                source_inp=source_inp,
                candidate_inp=candidate_inp,
                solver_inp=solver_inp,
                output_dir=output_dir,
                target_change=target_change,
            ),
        )

    def generate_codex_handoff(
        self,
        task_id: str,
        task_type: str,
        title: str | None = None,
        objective: str | None = None,
    ) -> dict[str, Any]:
        return self._safe(
            "generate_codex_handoff",
            lambda: cli.command_generate_codex_handoff(
                task_id=task_id,
                task_type=task_type,
                title=title,
                objective=objective,
            ),
        )

    def validate_codex_handoff(self, handoff_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "validate_codex_handoff",
            lambda: cli.command_validate_codex_handoff(handoff_dir=handoff_dir),
        )

    def intake_codex_result(self, handoff_dir: str | Path, result_json: str | Path) -> dict[str, Any]:
        return self._safe(
            "intake_codex_result",
            lambda: cli.command_intake_codex_result(handoff_dir=handoff_dir, result_json_path=result_json),
        )

    def report_acom_result_intake(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_acom_result_intake",
            lambda: cli.command_report_acom_result_intake(task_dir=task_dir),
        )

    def scaffold_acom_revalidation(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "scaffold_acom_revalidation",
            lambda: cli.command_scaffold_acom_revalidation(task_dir=task_dir),
        )

    def report_acom_revalidation(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_acom_revalidation",
            lambda: cli.command_report_acom_revalidation(task_dir=task_dir),
        )

    def execute_non_solver_revalidation(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "execute_non_solver_revalidation",
            lambda: cli.command_execute_non_solver_revalidation(task_dir=task_dir),
        )

    def report_non_solver_revalidation(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_non_solver_revalidation",
            lambda: cli.command_report_non_solver_revalidation(task_dir=task_dir),
        )

    def supervisor_review_non_solver_revalidation(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "supervisor_review_non_solver_revalidation",
            lambda: cli.command_supervisor_review_non_solver_revalidation(task_dir=task_dir),
        )

    def report_supervisor_non_solver_review(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_supervisor_non_solver_review",
            lambda: cli.command_report_supervisor_non_solver_review(task_dir=task_dir),
        )

    def report_codex_handoff(self, handoff_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_codex_handoff",
            lambda: cli.command_report_codex_handoff(handoff_dir=handoff_dir),
        )

    def list_acom_templates(self) -> dict[str, Any]:
        return self._safe("list_acom_templates", lambda: cli.command_list_acom_templates())

    def describe_acom_template(self, template_id: str) -> dict[str, Any]:
        return self._safe(
            "describe_acom_template",
            lambda: cli.command_describe_acom_template(template_id=template_id),
        )

    def generate_pipeline_acom_handoff(
        self,
        task_id: str,
        template_id: str,
        title: str | None = None,
        objective: str | None = None,
    ) -> dict[str, Any]:
        return self._safe(
            "generate_pipeline_acom_handoff",
            lambda: cli.command_generate_codex_handoff(
                task_id=task_id,
                template_id=template_id,
                title=title,
                objective=objective,
            ),
        )

    def validate_acom_template_pack(self) -> dict[str, Any]:
        return self._safe(
            "validate_acom_template_pack",
            lambda: cli.command_validate_acom_template_pack(),
        )

    def list_pipeline_agents(self) -> dict[str, Any]:
        return self._safe("list_pipeline_agents", lambda: cli.command_list_pipeline_agents())

    def scaffold_pipeline_task(self, task_id: str) -> dict[str, Any]:
        return self._safe(
            "scaffold_pipeline_task",
            lambda: cli.command_scaffold_pipeline_task(task_id=task_id, root=self.project_root),
        )

    def validate_pipeline_protocol(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "validate_pipeline_protocol",
            lambda: cli.command_validate_pipeline_protocol(task_dir=task_dir),
        )

    def report_pipeline_protocol(self, task_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_pipeline_protocol",
            lambda: cli.command_report_pipeline_protocol(task_dir=task_dir),
        )

    def queue_patch_preview_preflight(self, task_dir: str | Path, patch_preview_dir: str | Path | None = None) -> dict[str, Any]:
        return self._safe(
            "queue_patch_preview_preflight",
            lambda: cli.command_queue_patch_preview(
                task_dir=task_dir,
                patch_preview_dir=patch_preview_dir,
                mode="preflight-only",
            ),
        )

    def queue_patch_preview_dry_run(self, task_dir: str | Path, patch_preview_dir: str | Path | None = None) -> dict[str, Any]:
        return self._safe(
            "queue_patch_preview_dry_run",
            lambda: cli.command_queue_patch_preview(
                task_dir=task_dir,
                patch_preview_dir=patch_preview_dir,
                mode="dry-run-enqueue",
            ),
        )

    def create_patch_queue_approval_token(
        self,
        workflow_dir: str | Path,
        approved_by: str,
        approval_phrase: str,
        expires_hours: int = 24,
    ) -> dict[str, Any]:
        return self._safe(
            "create_patch_queue_approval_token",
            lambda: cli.command_approve_patch_queue(
                workflow_dir=workflow_dir,
                approved_by=approved_by,
                approval_phrase=approval_phrase,
                expires_hours=expires_hours,
            ),
        )

    def queue_patch_preview_real_queue_only(
        self,
        workflow_dir: str | Path,
        approval_token: str | Path,
    ) -> dict[str, Any]:
        return self._safe(
            "queue_patch_preview_real_queue_only",
            lambda: cli.command_queue_patch_preview(
                workflow_dir=workflow_dir,
                mode="real-queue-only",
                approval_token=approval_token,
            ),
        )

    def poll_patch_queue_status(self, workflow_dir: str | Path) -> dict[str, Any]:
        return self._safe("poll_patch_queue_status", lambda: cli.command_poll_patch_queue(workflow_dir=workflow_dir))

    def intake_patched_job_output(
        self,
        workflow_dir: str | Path,
        manual_odb_path: str | Path | None = None,
    ) -> dict[str, Any]:
        return self._safe(
            "intake_patched_job_output",
            lambda: cli.command_intake_patched_job_output(
                workflow_dir=workflow_dir,
                manual_odb_path=manual_odb_path,
            ),
        )

    def extract_patched_job_metrics(self, workflow_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "extract_patched_job_metrics",
            lambda: cli.command_extract_patched_job_metrics(workflow_dir=workflow_dir),
        )

    def report_patched_job(self, workflow_dir: str | Path) -> dict[str, Any]:
        return self._safe(
            "report_patched_job",
            lambda: cli.command_report_patched_job(workflow_dir=workflow_dir),
        )

    def prepare_controlled_solver_run(
        self,
        candidate_inp: str | Path,
        source_inp: str | Path,
        evidence_dir: str | Path,
        cpus: int = 14,
    ) -> dict[str, Any]:
        from abqpilot.solver import prepare_solver_run

        return self._safe(
            "prepare_controlled_solver_run",
            lambda: prepare_solver_run(
                candidate_inp=candidate_inp,
                source_inp=source_inp,
                evidence_dir=evidence_dir,
                cpus=cpus,
            ),
        )

    def approve_controlled_solver_run(
        self,
        solver_run_dir: str | Path,
        approved_by: str,
        approval_phrase: str,
        expires_hours: int = 24,
    ) -> dict[str, Any]:
        from abqpilot.solver import approve_solver_run

        return self._safe(
            "approve_controlled_solver_run",
            lambda: approve_solver_run(
                solver_run_dir=solver_run_dir,
                approved_by=approved_by,
                approval_phrase=approval_phrase,
                expires_hours=expires_hours,
            ),
        )

    def run_approved_solver(self, solver_run_dir: str | Path, approval_token: str | Path) -> dict[str, Any]:
        from abqpilot.solver import run_solver_approved

        return self._safe(
            "run_approved_solver",
            lambda: run_solver_approved(solver_run_dir=solver_run_dir, approval_token=approval_token),
        )

    def monitor_solver_run(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import monitor_solver_run

        return self._safe("monitor_solver_run", lambda: monitor_solver_run(solver_run_dir=solver_run_dir))

    def diagnose_job_output(self, solver_run_dir: str | Path, job_name: str) -> dict[str, Any]:
        from abqpilot.diagnostics import diagnose_job_output

        return self._safe(
            "diagnose_job_output",
            lambda: {
                "command": "diagnose_job_output",
                "verdict": "JOB_ODB_DIAGNOSIS_READY",
                "success": True,
                "details": diagnose_job_output(job_dir=solver_run_dir, job_name=job_name, write_artifacts=True),
                "errors": [],
                "warnings": [],
            },
        )

    def list_abqjobpilot_job_records(
        self,
        runtime_dir: str | Path,
        status: str | None = None,
        job_name: str | None = None,
        max_results: int | None = 20,
    ) -> dict[str, Any]:
        return self._safe(
            "list_abqjobpilot_job_records",
            lambda: cli.command_list_abqjobpilot_records(
                abqjobpilot_runtime_dir=runtime_dir,
                status=status,
                job_name=job_name,
                max_results=max_results,
            ),
        )

    def diagnose_from_abqjobpilot_record(
        self,
        report_json: str | Path | None = None,
        job_id: str | None = None,
        runtime_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        return self._safe(
            "diagnose_from_abqjobpilot_record",
            lambda: cli.command_diagnose_job_output(
                abqjobpilot_report=report_json,
                abqjobpilot_job_id=job_id,
                abqjobpilot_runtime_dir=runtime_dir,
            ),
        )

    def propose_solver_failure_repair(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.repair import propose_solver_failure_repair

        return self._safe("propose_solver_failure_repair", lambda: propose_solver_failure_repair(solver_run_dir=solver_run_dir))

    def intake_solver_output(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import intake_solver_run_output

        return self._safe("intake_solver_output", lambda: intake_solver_run_output(solver_run_dir=solver_run_dir))

    def report_solver_run(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import report_solver_run

        return self._safe("report_solver_run", lambda: report_solver_run(solver_run_dir=solver_run_dir))

    def prepare_dflux_guarded_solver_run(
        self,
        preview_inp: str | Path,
        validation_json: str | Path,
        output_root: str | Path | None = None,
    ) -> dict[str, Any]:
        from abqpilot.solver import prepare_dflux_guarded_solver_run

        return self._safe(
            "prepare_dflux_guarded_solver_run",
            lambda: prepare_dflux_guarded_solver_run(
                preview_inp=preview_inp,
                validation_json=validation_json,
                output_root=output_root or self.project_root / "runs" / "stage4_4_dflux_deactivated_controlled_solver_validation",
            ),
        )

    def approve_dflux_guarded_solver_run(self, solver_run_dir: str | Path, approval_phrase: str) -> dict[str, Any]:
        from abqpilot.solver import approve_dflux_guarded_solver_run

        return self._safe(
            "approve_dflux_guarded_solver_run",
            lambda: approve_dflux_guarded_solver_run(solver_run_dir=solver_run_dir, approval_phrase=approval_phrase, approved_by="human"),
        )

    def run_dflux_guarded_solver_approved(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import run_dflux_guarded_solver_approved

        return self._safe("run_dflux_guarded_solver_approved", lambda: run_dflux_guarded_solver_approved(solver_run_dir=solver_run_dir))

    def monitor_dflux_guarded_solver_run(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import monitor_dflux_guarded_solver_run

        return self._safe("monitor_dflux_guarded_solver_run", lambda: monitor_dflux_guarded_solver_run(solver_run_dir=solver_run_dir))

    def intake_dflux_guarded_solver_output(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import intake_dflux_guarded_solver_output

        return self._safe("intake_dflux_guarded_solver_output", lambda: intake_dflux_guarded_solver_output(solver_run_dir=solver_run_dir))

    def report_dflux_guarded_solver_run(self, solver_run_dir: str | Path) -> dict[str, Any]:
        from abqpilot.solver import report_dflux_guarded_solver_run

        return self._safe("report_dflux_guarded_solver_run", lambda: report_dflux_guarded_solver_run(solver_run_dir=solver_run_dir))

    def open_artifact_folder(self, path: str | Path) -> dict[str, Any]:
        target = Path(path)
        folder = target if target.is_dir() else target.parent
        return {
            "command": "open_artifact_folder",
            "verdict": "ARTIFACT_FOLDER_PATH_READY",
            "success": folder.exists(),
            "path": str(folder),
            "warnings": ["GUI Beta displays the folder path instead of launching an external process."],
            "errors": [] if folder.exists() else [f"folder does not exist: {folder}"],
        }

    def preview_artifact(self, path: str | Path | None) -> dict[str, Any]:
        return self._safe("preview_artifact", lambda: {"command": "preview_artifact", **preview_artifact(path)})

    def presets(self) -> dict[str, Any]:
        return {
            "command": "workflow_presets",
            "verdict": "WORKFLOW_PRESETS_READY",
            "success": True,
            "presets": workflow_presets(),
            "errors": [],
            "warnings": [],
        }

    def blocked_action(self, action_name: str) -> dict[str, Any]:
        return {
            "command": action_name,
            "verdict": BLOCKED_VERDICT,
            "success": False,
            "errors": ["This action is disabled in GUI Beta and requires a future gated stage."],
            "warnings": [],
        }

    def _load_task(self, task_dir: str | Path, refreshed: bool = False) -> dict[str, Any]:
        summary = load_task_summary(task_dir)
        view_model = build_task_view_model(task_dir)
        return {
            "command": "refresh_task" if refreshed else "load_task",
            "verdict": "TASK_VIEW_MODEL_READY",
            "success": True,
            "task_summary": summary,
            "view_model": view_model,
            "errors": [],
            "warnings": summary.get("errors", []),
        }

    def _safe(self, command: str, action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        try:
            result = action()
            result.setdefault("command", command)
            result.setdefault("success", True)
            result.setdefault("errors", [])
            result.setdefault("warnings", [])
            return result
        except Exception as exc:
            return {
                "command": command,
                "verdict": "GUI_ACTION_FAILED",
                "success": False,
                "errors": [str(exc)],
                "warnings": [],
            }
