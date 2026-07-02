from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.core.artifact_registry import ArtifactRegistry
from abqpilot.core.task_config import safety_flags


DEFAULT_STEP_NAMES = [
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

STEP_STATUSES = {
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "SKIPPED",
    "FAILED",
    "WAITING_FOR_MANUAL_ACTION",
    "STOPPED_BY_MODE_LIMIT",
}


class TaskWorkspace:
    def __init__(
        self,
        config: dict[str, Any],
        work_root: str | Path | None = None,
        task_id: str | None = None,
        step_names: list[str] | None = None,
    ) -> None:
        self.config = dict(config)
        self.task_id = task_id or generate_task_id(str(config.get("task_name", "abqpilot_task")))
        self.work_root = Path(work_root or config.get("work_root", "runs"))
        self.task_dir = self.work_root / "tasks" / self.task_id
        self.steps_dir = self.task_dir / "steps"
        self.step_names = step_names or DEFAULT_STEP_NAMES
        self.registry = ArtifactRegistry(self.task_id)
        self.state = self._new_state()

    @classmethod
    def load_existing(
        cls,
        config: dict[str, Any],
        work_root: str | Path | None,
        task_id: str,
        step_names: list[str] | None = None,
    ) -> "TaskWorkspace":
        workspace = cls(config=config, work_root=work_root, task_id=task_id, step_names=step_names)
        if not workspace.state_path.exists():
            raise FileNotFoundError(f"task state does not exist: {workspace.state_path}")
        if workspace.config_path.exists():
            workspace.config = json.loads(workspace.config_path.read_text(encoding="utf-8"))
        workspace.state = json.loads(workspace.state_path.read_text(encoding="utf-8"))
        workspace._ensure_state_shape()
        if workspace.artifacts_path.exists():
            workspace.registry = ArtifactRegistry.load(workspace.artifacts_path)
        return workspace

    def create(self) -> "TaskWorkspace":
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.steps_dir.mkdir(parents=True, exist_ok=True)
        for step_name in self.step_names:
            self.step_dir(step_name).mkdir(parents=True, exist_ok=True)
        self._ensure_state_shape()
        self.save_config()
        self.registry.add_artifact("source_cae", "input", self.config.get("cae_path") or "", None)
        self.save_artifacts()
        self.save_state()
        if not self.trace_path.exists():
            self.save_trace([])
        return self

    @property
    def config_path(self) -> Path:
        return self.task_dir / "task_config.json"

    @property
    def state_path(self) -> Path:
        return self.task_dir / "task_state.json"

    @property
    def artifacts_path(self) -> Path:
        return self.task_dir / "artifacts.json"

    @property
    def trace_path(self) -> Path:
        return self.task_dir / "pipeline_trace.json"

    @property
    def final_result_path(self) -> Path:
        return self.task_dir / "final_result.json"

    def step_dir(self, step_name: str) -> Path:
        return self.steps_dir / step_name

    def step_result_path(self, step_name: str) -> Path:
        return self.step_dir(step_name) / "step_result.json"

    def step_state(self, step_name: str) -> dict[str, Any]:
        return self.state["steps"][step_name]

    def save_config(self) -> None:
        _write_json(self.config_path, self.config)

    def save_state(self) -> None:
        self.state["updated_at"] = _now()
        _write_json(self.state_path, self.state)

    def save_artifacts(self) -> None:
        self.registry.save(self.artifacts_path)

    def load_trace(self) -> list[dict[str, Any]]:
        if not self.trace_path.exists():
            return []
        payload = json.loads(self.trace_path.read_text(encoding="utf-8"))
        return payload.get("events", [])

    def save_trace(self, events: list[dict[str, Any]]) -> None:
        _write_json(self.trace_path, {"task_id": self.task_id, "events": events})

    def save_final_result(self, result: dict[str, Any]) -> None:
        _write_json(self.final_result_path, result)

    def mark_step_running(self, step_name: str) -> None:
        step = self.step_state(step_name)
        step["status"] = "RUNNING"
        step["started_at"] = _now()
        step["finished_at"] = None
        self.state["status"] = "RUNNING"
        self.state["current_step"] = step_name
        self.state["stop_reason"] = None
        self.save_state()

    def mark_step_completed(self, step_name: str, verdict: str, result_path: str | Path) -> None:
        step = self.step_state(step_name)
        step["status"] = "COMPLETED"
        step["verdict"] = verdict
        step["result_path"] = self._relative_path(result_path)
        step["finished_at"] = _now()
        if step_name not in self.state["completed_steps"]:
            self.state["completed_steps"].append(step_name)
        if step_name in self.state["failed_steps"]:
            self.state["failed_steps"].remove(step_name)
        self.save_state()

    def mark_step_failed(self, step_name: str, verdict: str, result_path: str | Path | None = None) -> None:
        step = self.step_state(step_name)
        step["status"] = "FAILED"
        step["verdict"] = verdict
        if result_path is not None:
            step["result_path"] = self._relative_path(result_path)
        step["finished_at"] = _now()
        if step_name not in self.state["failed_steps"]:
            self.state["failed_steps"].append(step_name)
        self.save_state()

    def mark_step_waiting(self, step_name: str, verdict: str, result_path: str | Path | None = None) -> None:
        step = self.step_state(step_name)
        step["status"] = "WAITING_FOR_MANUAL_ACTION"
        step["verdict"] = verdict
        if result_path is not None:
            step["result_path"] = self._relative_path(result_path)
        step["finished_at"] = _now()
        self.save_state()

    def mark_step_skipped(self, step_name: str, verdict: str) -> None:
        step = self.step_state(step_name)
        if step["status"] != "COMPLETED":
            step["status"] = "SKIPPED"
            step["verdict"] = verdict
        if step_name not in self.state["skipped_steps"]:
            self.state["skipped_steps"].append(step_name)
        self.save_state()

    def increment_rerun_count(self, step_name: str) -> int:
        step = self.step_state(step_name)
        step["rerun_count"] = int(step.get("rerun_count", 0)) + 1
        self.save_state()
        return step["rerun_count"]

    def set_stop_reason(self, status: str, stop_reason: str) -> None:
        self.state["status"] = status
        self.state["stop_reason"] = stop_reason
        self.save_state()

    def stop_for_manual_solver(self) -> None:
        self.state["status"] = "WAITING_FOR_MANUAL_SOLVER"
        self.state["stop_reason"] = "NEED_MANUAL_SOLVER_OUTPUTS"
        self.state["requires_human_action"] = True
        self.state["human_action_reason"] = "Manual solver outputs are required before ODB metrics extraction."
        self.save_state()

    def stop_for_abqjobpilot_or_manual_solver(self) -> None:
        self.state["status"] = "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER"
        self.state["stop_reason"] = "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER"
        self.state["requires_human_action"] = True
        self.state["human_action_reason"] = "Queue enqueue completed; solver execution remains external/manual."
        self.save_state()

    def stop_failed(self, reason: str = "STEP_FAILED") -> None:
        self.state["status"] = "FAILED"
        self.state["stop_reason"] = reason
        self.save_state()

    def stop_by_mode_limit(self) -> None:
        self.state["status"] = "STOPPED_BY_MODE_LIMIT"
        self.state["stop_reason"] = "STOPPED_BY_MODE_LIMIT"
        self.state["requires_human_action"] = False
        self.state["human_action_reason"] = None
        self.save_state()

    def stop_completed(self) -> None:
        self.state["status"] = "COMPLETED"
        self.state["stop_reason"] = "PIPELINE_COMPLETED"
        self.state["requires_human_action"] = False
        self.state["human_action_reason"] = None
        self.save_state()

    def _new_state(self) -> dict[str, Any]:
        now = _now()
        state = {
            "task_id": self.task_id,
            "task_name": self.config.get("task_name", "abqpilot_task"),
            "created_at": now,
            "updated_at": now,
            "status": "CREATED",
            "current_step": None,
            "stop_reason": None,
            "steps": {},
            "completed_steps": [],
            "failed_steps": [],
            "skipped_steps": [],
            "requires_human_action": False,
            "human_action_reason": None,
            "safety_flags": {
                "allow_solver_submit": False,
                "allow_abqjobpilot": False,
                "allow_abqjobpilot_preflight": False,
                "allow_abqjobpilot_dry_run_enqueue": False,
                "allow_jobpilot_enqueue_authorization": False,
                "allow_abqjobpilot_real_enqueue": safety_flags(self.config).get("allow_abqjobpilot_real_enqueue", False),
                "allow_abqjobpilot_status_poll": safety_flags(self.config).get("allow_abqjobpilot_status_poll", False),
                "allow_llm": False,
                "allow_codex_runtime": False,
            },
        }
        state["safety_flags"].update(
            {
                "allow_cae_export": safety_flags(self.config).get("allow_cae_export", False),
                "allow_odb_read": safety_flags(self.config).get("allow_odb_read", False),
                "allow_abqjobpilot_preflight": safety_flags(self.config).get("allow_abqjobpilot_preflight", False),
                "allow_abqjobpilot_dry_run_enqueue": safety_flags(self.config).get(
                    "allow_abqjobpilot_dry_run_enqueue", False
                ),
                "allow_jobpilot_enqueue_authorization": safety_flags(self.config).get(
                    "allow_jobpilot_enqueue_authorization", False
                ),
                "allow_abqjobpilot_real_enqueue": False,
                "allow_abqjobpilot_status_poll": safety_flags(self.config).get("allow_abqjobpilot_status_poll", False),
            }
        )
        return state

    def _ensure_state_shape(self) -> None:
        self.state.setdefault("stop_reason", None)
        self.state.setdefault("steps", {})
        self.state.setdefault("completed_steps", [])
        self.state.setdefault("failed_steps", [])
        self.state.setdefault("skipped_steps", [])
        self.state.setdefault("requires_human_action", False)
        self.state.setdefault("human_action_reason", None)
        self.state.setdefault("safety_flags", {})
        self.state["safety_flags"].setdefault("allow_solver_submit", False)
        self.state["safety_flags"].setdefault("allow_abqjobpilot", False)
        self.state["safety_flags"].setdefault("allow_abqjobpilot_preflight", False)
        self.state["safety_flags"].setdefault("allow_abqjobpilot_dry_run_enqueue", False)
        self.state["safety_flags"].setdefault("allow_jobpilot_enqueue_authorization", False)
        self.state["safety_flags"].setdefault("allow_abqjobpilot_real_enqueue", False)
        self.state["safety_flags"].setdefault("allow_abqjobpilot_status_poll", False)
        self.state["safety_flags"].setdefault("allow_llm", False)
        self.state["safety_flags"].setdefault("allow_codex_runtime", False)
        for step_name in self.step_names:
            self.state["steps"].setdefault(step_name, _default_step_state())

    def _relative_path(self, path: str | Path) -> str:
        target = Path(path)
        try:
            return str(target.relative_to(self.task_dir))
        except ValueError:
            return str(target)


def generate_task_id(task_name: str) -> str:
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in task_name.lower()).strip("_") or "abqpilot_task"
    return f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def _default_step_state() -> dict[str, Any]:
    return {
        "status": "PENDING",
        "verdict": None,
        "result_path": None,
        "started_at": None,
        "finished_at": None,
        "rerun_count": 0,
    }


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
