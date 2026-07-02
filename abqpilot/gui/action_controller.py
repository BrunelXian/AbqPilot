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
