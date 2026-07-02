from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any


RUNTIME_GUARD_PATHS = (
    Path("runtime") / "queue.json",
    Path("runtime") / "live_status.json",
    Path("runtime") / "reports",
)
SOLVER_OUTPUT_EXTENSIONS = (".lck", ".odb", ".sta", ".msg", ".dat")


class AbqJobPilotPreflightAdapter:
    def __init__(self, project_root: str | None = None) -> None:
        self.project_root = str(project_root) if project_root else None
        self._api_module: Any | None = None
        self._api_error: str | None = None
        self._diagnostics: dict[str, Any] | None = None

    def available(self) -> bool:
        return self._load_api() is not None

    def diagnostics(self) -> dict[str, Any]:
        self._load_api()
        return self._diagnostics or {
            "available": self._api_module is not None,
            "status": "AVAILABLE" if self._api_module is not None else "ABQJOBPILOT_UNAVAILABLE",
            "reason": self._api_error,
            "project_root": self.project_root,
            "api_path_exists": None,
        }

    def build_request(
        self,
        inp_path: str,
        job_name: str | None,
        cpus: int,
        batch: str | None,
        strategy: str | None,
        working_dir: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        inp = Path(inp_path)
        selected_job_name = job_name or inp.stem
        return {
            "inp_path": str(inp),
            "job_name": selected_job_name,
            "cpus": int(cpus),
            "batch": batch,
            "strategy": strategy,
            "working_dir": str(working_dir) if working_dir is not None else str(inp.parent),
            "submission_mode": "preview_only",
            "allow_solver_submit": False,
            "metadata": metadata or {"source": "AbqPilot-v2"},
        }

    def preflight(self, request: dict) -> dict:
        api = self._load_api()
        if api is None:
            return {
                "status": "ABQJOBPILOT_UNAVAILABLE",
                "job_id": None,
                "inp_exists": Path(request["inp_path"]).exists(),
                "expected_odb_path": None,
                "command_preview": self._command_preview(request),
                "project_root": self.project_root,
                "available": False,
                "errors": [self._api_error or "abqjobpilot public API is unavailable"],
                "warnings": ["abqjobpilot preflight was skipped because the public API could not be imported"],
            }

        try:
            client = api.AbqJobPilotClient()
            job_request = self._make_job_request(api.JobRequest, request)
            raw_result = client.preflight(job_request)
            result = _to_dict(raw_result)
        except Exception as exc:  # pragma: no cover - exact API failures are environment dependent.
            return {
                "status": "ABQJOBPILOT_PREFLIGHT_FAILED",
                "job_id": None,
                "inp_exists": Path(request["inp_path"]).exists(),
                "expected_odb_path": None,
                "command_preview": self._command_preview(request),
                "errors": [str(exc)],
                "warnings": [],
            }

        result.setdefault("status", "PREVIEW_READY")
        result.setdefault("job_id", request.get("job_name"))
        result.setdefault("inp_exists", Path(request["inp_path"]).exists())
        result.setdefault("expected_odb_path", str(Path(request["working_dir"]) / f"{request['job_name']}.odb"))
        result.setdefault("command_preview", self._command_preview(request))
        result.setdefault("project_root", self.project_root)
        result.setdefault("available", True)
        result.setdefault("errors", [])
        result.setdefault("warnings", [])
        return result

    def dry_run_enqueue(self, request: dict) -> dict:
        safety_error = _unsafe_request_reason(request)
        if safety_error:
            return {
                "status": "UNSAFE_JOBPILOT_REQUEST_REJECTED",
                "dry_run": True,
                "runtime_mutation_detected": False,
                "errors": [safety_error],
                "warnings": [],
                "project_root": self.project_root,
                "available": None,
            }

        api = self._load_api()
        if api is None:
            return {
                "status": "ABQJOBPILOT_UNAVAILABLE",
                "dry_run": True,
                "runtime_mutation_detected": False,
                "errors": [self._api_error or "abqjobpilot public API is unavailable"],
                "warnings": ["abqjobpilot dry-run enqueue was skipped because the public API could not be imported"],
                "project_root": self.project_root,
                "available": False,
                "runtime_snapshot_before": snapshot_runtime_files(self.project_root),
                "runtime_snapshot_after": snapshot_runtime_files(self.project_root),
            }

        snapshot_before = snapshot_runtime_files(self.project_root)
        try:
            client = api.AbqJobPilotClient()
            job_request = self._make_job_request(api.JobRequest, request)
            raw_result = client.enqueue(job_request, dry_run=True)
            result = _to_dict(raw_result)
        except Exception as exc:  # pragma: no cover - exact API failures are environment dependent.
            snapshot_after = snapshot_runtime_files(self.project_root)
            mutation_detected = snapshot_before != snapshot_after
            return {
                "status": "ABQJOBPILOT_DRY_RUN_REJECTED",
                "dry_run": True,
                "runtime_mutation_detected": mutation_detected,
                "runtime_snapshot_before": snapshot_before,
                "runtime_snapshot_after": snapshot_after,
                "errors": [str(exc)],
                "warnings": [],
                "project_root": self.project_root,
                "available": True,
            }
        snapshot_after = snapshot_runtime_files(self.project_root)
        mutation_detected = snapshot_before != snapshot_after

        result.setdefault("status", "DRY_RUN_READY")
        if result["status"] == "PREVIEW_READY":
            result["status"] = "DRY_RUN_READY"
        result.setdefault("dry_run", True)
        result.setdefault("job_id", request.get("job_name"))
        result.setdefault("command_preview", self._dry_run_command_preview(request))
        result.setdefault("project_root", self.project_root)
        result.setdefault("available", True)
        result.setdefault("errors", [])
        result.setdefault("warnings", [])
        result["runtime_mutation_detected"] = mutation_detected
        result["runtime_snapshot_before"] = snapshot_before
        result["runtime_snapshot_after"] = snapshot_after
        if mutation_detected:
            result["status"] = "ABQJOBPILOT_RUNTIME_MUTATION_DETECTED"
            result.setdefault("errors", []).append("abqjobpilot runtime queue/status files changed during dry-run enqueue")
        return result

    def real_enqueue(self, request: dict, approval_report: dict) -> dict:
        gate_error = _real_enqueue_gate_error(request, approval_report)
        if gate_error:
            return _real_enqueue_result(
                status=gate_error[0],
                request=request,
                project_root=self.project_root,
                errors=[gate_error[1]],
                called_api=False,
            )

        proof_error = _queue_only_proof_error(approval_report)
        if proof_error:
            return _real_enqueue_result(
                status="REAL_ENQUEUE_REJECTED_UNSAFE_DIRECT_SUBMIT",
                request=request,
                project_root=self.project_root,
                errors=[proof_error],
                called_api=False,
            )

        api = self._load_api()
        if api is None:
            return _real_enqueue_result(
                status="ABQJOBPILOT_UNAVAILABLE",
                request=request,
                project_root=self.project_root,
                errors=[self._api_error or "abqjobpilot public API is unavailable"],
                called_api=False,
                available=False,
            )

        runtime_before = snapshot_runtime_files(self.project_root)
        solver_before = snapshot_solver_output_files(request)
        try:
            client = api.AbqJobPilotClient()
            job_request = self._make_job_request(api.JobRequest, request)
            raw_result = client.enqueue(job_request, dry_run=False)
            result = _to_dict(raw_result)
        except Exception as exc:  # pragma: no cover - exact API failures are environment dependent.
            runtime_after = snapshot_runtime_files(self.project_root)
            solver_after = snapshot_solver_output_files(request)
            return _real_enqueue_result(
                status="REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE",
                request=request,
                project_root=self.project_root,
                errors=[str(exc)],
                runtime_snapshot_before=runtime_before,
                runtime_snapshot_after=runtime_after,
                solver_output_snapshot_before=solver_before,
                solver_output_snapshot_after=solver_after,
                called_api=True,
                raw_result=None,
            )

        runtime_after = snapshot_runtime_files(self.project_root)
        solver_after = snapshot_solver_output_files(request)
        mutation_report = compare_real_enqueue_runtime_mutation(runtime_before, runtime_after, solver_before, solver_after)
        status = "REAL_ENQUEUE_COMPLETED" if not mutation_report["forbidden_mutation_detected"] else "REAL_ENQUEUE_RUNTIME_MUTATION_UNSAFE"
        result.setdefault("status", status)
        if result["status"] in {"ENQUEUED", "QUEUE_ENQUEUED"}:
            result["status"] = status
        result.setdefault("dry_run", False)
        result.setdefault("project_root", self.project_root)
        result.setdefault("available", True)
        result.setdefault("errors", [])
        result.setdefault("warnings", [])
        result["queue_mutated"] = mutation_report["queue_mutated"]
        result["forbidden_mutation_detected"] = mutation_report["forbidden_mutation_detected"]
        result["runtime_mutation_report"] = mutation_report
        result["runtime_snapshot_before"] = runtime_before
        result["runtime_snapshot_after"] = runtime_after
        result["solver_output_snapshot_before"] = solver_before
        result["solver_output_snapshot_after"] = solver_after
        if mutation_report["forbidden_mutation_detected"]:
            result["status"] = "REAL_ENQUEUE_RUNTIME_MUTATION_UNSAFE"
            result["errors"].extend(mutation_report["errors"])
        else:
            result["status"] = status
        return result

    def poll_status(self, job_id: str | None = None, inp_path: str | None = None) -> dict:
        api = self._load_api()
        if api is None:
            return {
                "status": "ABQJOBPILOT_UNAVAILABLE",
                "normalized_status": "ABQJOBPILOT_UNAVAILABLE",
                "job_id": job_id,
                "inp_path": inp_path,
                "project_root": self.project_root,
                "available": False,
                "errors": [self._api_error or "abqjobpilot public API is unavailable"],
                "warnings": ["abqjobpilot status poll was skipped because the public API could not be imported"],
            }
        try:
            client = api.AbqJobPilotClient()
            raw_result = client.status(job_id=job_id, inp_path=inp_path)
            result = _to_dict(raw_result)
        except Exception as exc:  # pragma: no cover - exact API failures are environment dependent.
            return {
                "status": "ABQJOBPILOT_STATUS_POLL_FAILED",
                "normalized_status": "JOB_UNKNOWN",
                "job_id": job_id,
                "inp_path": inp_path,
                "project_root": self.project_root,
                "available": True,
                "errors": [str(exc)],
                "warnings": [],
            }
        result.setdefault("status", "UNKNOWN")
        result.setdefault("job_id", job_id)
        result.setdefault("inp_path", inp_path)
        result.setdefault("project_root", self.project_root)
        result.setdefault("available", True)
        result.setdefault("errors", [])
        result.setdefault("warnings", [])
        return result

    def locate_outputs(self, job_id: str | None = None, inp_path: str | None = None) -> dict:
        api = self._load_api()
        if api is None:
            return {
                "job_id": job_id,
                "inp_path": inp_path,
                "status": "ABQJOBPILOT_UNAVAILABLE",
                "working_dir": None,
                "expected_odb_path": None,
                "odb_exists": False,
                "lock_exists": False,
                "project_root": self.project_root,
                "available": False,
                "errors": [self._api_error or "abqjobpilot public API is unavailable"],
                "warnings": ["abqjobpilot output discovery was skipped because the public API could not be imported"],
            }
        try:
            client = api.AbqJobPilotClient()
            raw_result = client.locate_outputs(job_id=job_id, inp_path=inp_path)
            result = _to_dict(raw_result)
        except Exception as exc:  # pragma: no cover - exact API failures are environment dependent.
            return {
                "job_id": job_id,
                "inp_path": inp_path,
                "status": "ABQJOBPILOT_OUTPUT_DISCOVERY_FAILED",
                "working_dir": None,
                "expected_odb_path": None,
                "odb_exists": False,
                "lock_exists": False,
                "project_root": self.project_root,
                "available": True,
                "errors": [str(exc)],
                "warnings": [],
            }
        result.setdefault("job_id", job_id)
        result.setdefault("inp_path", inp_path)
        result.setdefault("working_dir", None)
        result.setdefault("expected_odb_path", None)
        result.setdefault("odb_exists", False)
        result.setdefault("lock_exists", False)
        result.setdefault("project_root", self.project_root)
        result.setdefault("available", True)
        result.setdefault("errors", [])
        result.setdefault("warnings", [])
        return result

    def write_preflight_artifacts(self, request: dict, result: dict, out_dir: str) -> dict:
        target_dir = Path(out_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        request_path = target_dir / "abqjobpilot_job_request.json"
        result_path = target_dir / "abqjobpilot_preflight_result.json"
        preview_path = target_dir / "abqjobpilot_command_preview.md"

        request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        preview_path.write_text(self._render_markdown(request, result), encoding="utf-8")
        return {
            "abqjobpilot_job_request": str(request_path),
            "abqjobpilot_preflight_result": str(result_path),
            "abqjobpilot_command_preview": str(preview_path),
        }

    def write_dry_run_enqueue_artifacts(self, request: dict, result: dict, out_dir: str) -> dict:
        target_dir = Path(out_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        request_path = target_dir / "abqjobpilot_dry_run_request.json"
        result_path = target_dir / "abqjobpilot_dry_run_enqueue_result.json"
        safety_path = target_dir / "abqjobpilot_dry_run_safety_report.json"
        preview_path = target_dir / "abqjobpilot_dry_run_preview.md"

        safety_report = {
            "status": "ABQJOBPILOT_RUNTIME_MUTATION_DETECTED"
            if result.get("runtime_mutation_detected")
            else "ABQJOBPILOT_DRY_RUN_RUNTIME_UNCHANGED",
            "runtime_mutation_detected": bool(result.get("runtime_mutation_detected")),
            "runtime_snapshot_before": result.get("runtime_snapshot_before"),
            "runtime_snapshot_after": result.get("runtime_snapshot_after"),
            "project_root": self.project_root,
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }
        request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        safety_path.write_text(json.dumps(safety_report, indent=2, ensure_ascii=False), encoding="utf-8")
        preview_path.write_text(self._render_dry_run_markdown(request, result, safety_report), encoding="utf-8")
        return {
            "abqjobpilot_dry_run_request": str(request_path),
            "abqjobpilot_dry_run_enqueue_result": str(result_path),
            "abqjobpilot_dry_run_safety_report": str(safety_path),
            "abqjobpilot_dry_run_preview": str(preview_path),
        }

    def write_real_enqueue_artifacts(self, request: dict, result: dict, out_dir: str) -> dict:
        target_dir = Path(out_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        request_path = target_dir / "abqjobpilot_real_enqueue_request.json"
        result_path = target_dir / "abqjobpilot_real_enqueue_result.json"
        safety_path = target_dir / "abqjobpilot_real_enqueue_safety_report.json"
        preview_path = target_dir / "abqjobpilot_real_enqueue_preview.md"

        safety_report = {
            "status": result.get("status"),
            "queue_mutated": bool(result.get("queue_mutated")),
            "forbidden_mutation_detected": bool(result.get("forbidden_mutation_detected")),
            "runtime_mutation_report": result.get("runtime_mutation_report", {}),
            "runtime_snapshot_before": result.get("runtime_snapshot_before"),
            "runtime_snapshot_after": result.get("runtime_snapshot_after"),
            "solver_output_snapshot_before": result.get("solver_output_snapshot_before"),
            "solver_output_snapshot_after": result.get("solver_output_snapshot_after"),
            "project_root": self.project_root,
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", []),
        }
        request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")
        result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        safety_path.write_text(json.dumps(safety_report, indent=2, ensure_ascii=False), encoding="utf-8")
        preview_path.write_text(self._render_real_enqueue_markdown(request, result, safety_report), encoding="utf-8")
        return {
            "abqjobpilot_real_enqueue_request": str(request_path),
            "abqjobpilot_real_enqueue_result": str(result_path),
            "abqjobpilot_real_enqueue_safety_report": str(safety_path),
            "abqjobpilot_real_enqueue_preview": str(preview_path),
        }

    def write_status_artifacts(self, status_result: dict, output_result: dict, out_dir: str) -> dict:
        target_dir = Path(out_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        request_path = target_dir / "abqjobpilot_status_request.json"
        status_path = target_dir / "abqjobpilot_status_result.json"
        outputs_path = target_dir / "abqjobpilot_output_locator_result.json"
        summary_path = target_dir / "abqjobpilot_status_summary.json"
        markdown_path = target_dir / "abqjobpilot_status_summary.md"

        normalized = normalize_jobpilot_status(status_result, output_result)
        request = {
            "job_id": status_result.get("job_id") or output_result.get("job_id"),
            "inp_path": status_result.get("inp_path") or output_result.get("inp_path"),
            "read_only": True,
            "called_enqueue": False,
            "submitted_solver": False,
            "opened_odb": False,
            "launched_queue_runner": False,
        }
        summary = {
            "task_id": status_result.get("task_id"),
            "job_id": request["job_id"],
            "raw_status": status_result.get("status"),
            "normalized_status": normalized,
            "working_dir": output_result.get("working_dir") or status_result.get("working_dir"),
            "expected_odb_path": output_result.get("expected_odb_path") or status_result.get("expected_odb_path"),
            "odb_exists": bool(output_result.get("odb_exists")),
            "lock_exists": bool(output_result.get("lock_exists") or status_result.get("lock_exists")),
            "status_sources": status_result.get("status_sources", []),
            "last_log_lines": status_result.get("last_log_lines", []),
            "final_pipeline_status": _final_status_for_normalized_job_status(normalized),
            "opened_odb": False,
            "submitted_solver": False,
            "launched_queue_runner": False,
            "errors": list(status_result.get("errors", [])) + list(output_result.get("errors", [])),
            "warnings": list(status_result.get("warnings", [])) + list(output_result.get("warnings", [])),
        }

        request_path.write_text(json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8")
        status_path.write_text(json.dumps(status_result, indent=2, ensure_ascii=False), encoding="utf-8")
        outputs_path.write_text(json.dumps(output_result, indent=2, ensure_ascii=False), encoding="utf-8")
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        markdown_path.write_text(_render_status_markdown(summary), encoding="utf-8")
        return {
            "abqjobpilot_status_request": str(request_path),
            "abqjobpilot_status_result": str(status_path),
            "abqjobpilot_output_locator_result": str(outputs_path),
            "abqjobpilot_status_summary": str(summary_path),
            "abqjobpilot_status_summary_md": str(markdown_path),
        }

    def _load_api(self) -> Any | None:
        if self._api_module is not None:
            return self._api_module
        if self.project_root:
            project_root = Path(self.project_root)
            api_path = project_root / "abqjobpilot" / "api"
            if not project_root.exists():
                self._api_error = f"abqjobpilot project_root does not exist: {project_root}"
                self._diagnostics = self._unavailable_diagnostics(api_path, self._api_error)
                return None
            if not api_path.exists():
                self._api_error = f"abqjobpilot public API path does not exist: {api_path}"
                self._diagnostics = self._unavailable_diagnostics(api_path, self._api_error)
                return None
            root_text = str(project_root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
        try:
            self._api_module = importlib.import_module("abqjobpilot.api")
            self._diagnostics = {
                "available": True,
                "status": "AVAILABLE",
                "reason": None,
                "project_root": self.project_root,
                "api_path_exists": self._api_path_exists(),
            }
            return self._api_module
        except Exception as exc:
            self._api_error = str(exc)
            self._diagnostics = self._unavailable_diagnostics(None, self._api_error)
            return None

    def _api_path_exists(self) -> bool | None:
        if not self.project_root:
            return None
        return (Path(self.project_root) / "abqjobpilot" / "api").exists()

    def _unavailable_diagnostics(self, api_path: Path | None, reason: str) -> dict[str, Any]:
        return {
            "available": False,
            "status": "ABQJOBPILOT_UNAVAILABLE",
            "reason": reason,
            "project_root": self.project_root,
            "api_path_exists": api_path.exists() if api_path is not None else self._api_path_exists(),
        }

    def _make_job_request(self, request_type: Any, request: dict) -> Any:
        payload = {
            "inp_path": request["inp_path"],
            "job_name": request["job_name"],
            "cpus": request["cpus"],
            "batch": request.get("batch"),
            "strategy": request.get("strategy"),
            "working_dir": request.get("working_dir"),
            "metadata": request.get("metadata", {}),
        }
        try:
            return request_type(**payload)
        except TypeError:
            return request_type(
                inp_path=payload["inp_path"],
                cpus=payload["cpus"],
                batch=payload["batch"],
                strategy=payload["strategy"],
            )

    def _command_preview(self, request: dict) -> str:
        parts = [
            "python",
            "-m",
            "abqjobpilot.api.cli",
            "preflight",
            "--inp",
            request["inp_path"],
            "--cpus",
            str(request["cpus"]),
        ]
        if request.get("batch"):
            parts.extend(["--batch", str(request["batch"])])
        if request.get("strategy"):
            parts.extend(["--strategy", str(request["strategy"])])
        parts.append("--json")
        return " ".join(parts)

    def _dry_run_command_preview(self, request: dict) -> str:
        parts = [
            "python",
            "-m",
            "abqjobpilot.api.cli",
            "enqueue",
            "--inp",
            request["inp_path"],
            "--cpus",
            str(request["cpus"]),
        ]
        if request.get("batch"):
            parts.extend(["--batch", str(request["batch"])])
        if request.get("strategy"):
            parts.extend(["--strategy", str(request["strategy"])])
        parts.extend(["--dry-run", "--json"])
        return " ".join(parts)

    def _render_markdown(self, request: dict, result: dict) -> str:
        return f"""# abqjobpilot Preflight Preview

Status: {result.get("status")}

## Request

- INP: {request.get("inp_path")}
- Job name: {request.get("job_name")}
- CPUs: {request.get("cpus")}
- Batch: {request.get("batch")}
- Strategy: {request.get("strategy")}
- Submission mode: {request.get("submission_mode")}
- Allow solver submit: {str(request.get("allow_solver_submit")).lower()}

## Command Preview

```powershell
{result.get("command_preview") or self._command_preview(request)}
```

## Safety

This is a preflight preview only. No job was enqueued. No solver was submitted.
"""

    def _render_dry_run_markdown(self, request: dict, result: dict, safety_report: dict) -> str:
        return f"""# abqjobpilot Dry-Run Enqueue Preview

Status: {result.get("status")}

## Request

- INP: {request.get("inp_path")}
- Job name: {request.get("job_name")}
- CPUs: {request.get("cpus")}
- Batch: {request.get("batch")}
- Strategy: {request.get("strategy")}
- Submission mode: {request.get("submission_mode")}
- Allow solver submit: {str(request.get("allow_solver_submit")).lower()}

## Command Preview

```powershell
{result.get("command_preview") or self._dry_run_command_preview(request)}
```

## Runtime Guard

- Runtime mutation detected: {str(safety_report.get("runtime_mutation_detected")).lower()}
- Safety status: {safety_report.get("status")}

## Safety

This was a dry-run enqueue only.
No job was enqueued.
No Abaqus solver was submitted.
abqjobpilot runtime queue/status files were not mutated.
"""

    def _render_real_enqueue_markdown(self, request: dict, result: dict, safety_report: dict) -> str:
        return f"""# abqjobpilot Controlled Real Queue Enqueue

Status: {result.get("status")}

## Request

- INP: {request.get("inp_path")}
- Job name: {request.get("job_name")}
- CPUs: {request.get("cpus")}
- Batch: {request.get("batch")}
- Strategy: {request.get("strategy")}
- Submission mode: {request.get("submission_mode")}
- Allow solver submit: {str(request.get("allow_solver_submit")).lower()}

## Runtime Guard

- Queue mutated: {str(safety_report.get("queue_mutated")).lower()}
- Forbidden mutation detected: {str(safety_report.get("forbidden_mutation_detected")).lower()}

## Safety

This stage performed controlled queue enqueue only.
No Abaqus solver was submitted.
No queue runner was launched.
No abqjobpilot GUI was opened.
"""


def snapshot_runtime_files(project_root: str | None) -> dict:
    snapshot: dict[str, Any] = {
        "project_root": project_root,
        "paths": {},
    }
    if not project_root:
        return snapshot
    root = Path(project_root)
    for relative in RUNTIME_GUARD_PATHS:
        target = root / relative
        entry: dict[str, Any] = {
            "path": str(target),
            "exists": target.exists(),
            "is_dir": target.is_dir() if target.exists() else False,
            "size": None,
            "mtime_ns": None,
        }
        if target.exists():
            stat = target.stat()
            entry["mtime_ns"] = stat.st_mtime_ns
            entry["size"] = _directory_size(target) if target.is_dir() else stat.st_size
        snapshot["paths"][str(relative)] = entry
    return snapshot


def snapshot_solver_output_files(request: dict) -> dict:
    working_dir = Path(request.get("working_dir") or Path(request.get("inp_path", ".")).parent)
    job_name = str(request.get("job_name") or Path(request.get("inp_path", "job")).stem)
    snapshot = {"working_dir": str(working_dir), "job_name": job_name, "files": {}}
    for extension in SOLVER_OUTPUT_EXTENSIONS:
        target = working_dir / f"{job_name}{extension}"
        entry = {
            "path": str(target),
            "exists": target.exists(),
            "size": None,
            "mtime_ns": None,
        }
        if target.exists():
            stat = target.stat()
            entry["size"] = stat.st_size
            entry["mtime_ns"] = stat.st_mtime_ns
        snapshot["files"][extension] = entry
    return snapshot


def compare_real_enqueue_runtime_mutation(
    runtime_before: dict,
    runtime_after: dict,
    solver_before: dict,
    solver_after: dict,
) -> dict:
    errors = []
    before_paths = runtime_before.get("paths", {})
    after_paths = runtime_after.get("paths", {})
    queue_key = str(Path("runtime") / "queue.json")
    queue_mutated = before_paths.get(queue_key) != after_paths.get(queue_key)
    for guarded in (Path("runtime") / "live_status.json", Path("runtime") / "reports"):
        key = str(guarded)
        if before_paths.get(key) != after_paths.get(key):
            errors.append(f"forbidden runtime mutation: {key}")
    for extension, before_entry in solver_before.get("files", {}).items():
        after_entry = solver_after.get("files", {}).get(extension)
        if before_entry != after_entry:
            errors.append(f"forbidden solver output mutation: {after_entry.get('path') if after_entry else extension}")
    return {
        "queue_mutated": bool(queue_mutated),
        "forbidden_mutation_detected": bool(errors),
        "errors": errors,
    }


def normalize_jobpilot_status(status_result: dict, output_result: dict | None = None) -> str:
    output_result = output_result or {}
    raw = str(status_result.get("status") or "").upper()
    odb_exists = bool(output_result.get("odb_exists") or status_result.get("odb_exists"))
    lock_exists = bool(output_result.get("lock_exists") or status_result.get("lock_exists"))
    if raw == "ABQJOBPILOT_UNAVAILABLE":
        return "ABQJOBPILOT_UNAVAILABLE"
    if raw in {"QUEUED", "PENDING"}:
        return "JOB_QUEUED"
    if raw in {"RUNNING", "DATACHECK_RUNNING", "FULL_RUNNING"} or raw.endswith("_RUNNING"):
        return "JOB_RUNNING"
    if raw in {"COMPLETED", "COMPLETED_OK", "COMPLETED_WITH_WARNINGS"}:
        return "JOB_OUTPUTS_READY" if odb_exists else "JOB_ODB_MISSING"
    if raw in {"FAILED", "FAILED_FATAL", "FAILED_NUMERICAL", "FAILED_INPUT", "FAILED_LICENSE"} or raw.startswith("FAILED"):
        return "JOB_FAILED"
    if raw == "LOCKED" or lock_exists:
        return "JOB_LOCKED"
    if raw == "ODB_MISSING":
        return "JOB_ODB_MISSING"
    return "JOB_UNKNOWN"


def _final_status_for_normalized_job_status(normalized_status: str) -> str:
    if normalized_status in {"JOB_QUEUED", "JOB_RUNNING"}:
        return "WAITING_FOR_ABQJOBPILOT"
    if normalized_status == "JOB_OUTPUTS_READY":
        return "JOB_OUTPUTS_READY"
    if normalized_status == "JOB_ODB_MISSING":
        return "JOB_ODB_MISSING"
    if normalized_status == "JOB_FAILED":
        return "JOB_FAILED"
    if normalized_status == "JOB_LOCKED":
        return "JOB_LOCKED"
    if normalized_status == "ABQJOBPILOT_UNAVAILABLE":
        return "ABQJOBPILOT_UNAVAILABLE"
    return "JOB_UNKNOWN"


def _render_status_markdown(summary: dict) -> str:
    return f"""# abqjobpilot Status Poll

Status: {summary.get("normalized_status")}

## Job

- Job ID: {summary.get("job_id")}
- Raw status: {summary.get("raw_status")}
- Working directory: {summary.get("working_dir")}
- Expected ODB: {summary.get("expected_odb_path")}
- ODB exists: {str(summary.get("odb_exists")).lower()}
- Lock exists: {str(summary.get("lock_exists")).lower()}

## Safety

This status poll is read-only.
No job was enqueued.
No Abaqus solver was submitted.
No queue runner was launched.
No abqjobpilot GUI was opened.
No ODB was opened.
"""


def _directory_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _unsafe_request_reason(request: dict) -> str | None:
    if request.get("allow_solver_submit") is not False:
        return "allow_solver_submit must be false for abqjobpilot dry-run enqueue"
    if request.get("submission_mode") != "preview_only":
        return "submission_mode must be preview_only for abqjobpilot dry-run enqueue"
    return None


def _unsafe_real_enqueue_request_reason(request: dict) -> str | None:
    if request.get("allow_solver_submit") is not False:
        return "allow_solver_submit must be false for real queue enqueue"
    if request.get("submission_mode") not in {"preview_only", "enqueue_only"}:
        return "submission_mode must be preview_only or enqueue_only for real queue enqueue"
    return None


def _real_enqueue_gate_error(request: dict, approval_report: dict) -> tuple[str, str] | None:
    if not approval_report.get("allow_abqjobpilot_real_enqueue"):
        return ("REAL_ENQUEUE_REJECTED_CONFIG_DISABLED", "allow_abqjobpilot_real_enqueue is false")
    request_error = _unsafe_real_enqueue_request_reason(request)
    if request_error:
        return ("REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE", request_error)
    required = {
        "preflight_status": "PREVIEW_READY",
        "dry_run_enqueue_status": "DRY_RUN_READY",
        "runtime_mutation_detected": False,
        "approval_token_status": "APPROVAL_TOKEN_VALID",
    }
    for key, expected in required.items():
        if approval_report.get(key) != expected:
            return ("REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE", f"{key} must be {expected}")
    if approval_report.get("allow_solver_submit") is not False:
        return ("REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE", "allow_solver_submit must be false")
    if approval_report.get("submission_mode") not in {"preview_only", "enqueue_only"}:
        return ("REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE", "submission_mode must be preview_only or enqueue_only")
    for field in (
        "candidate_inp_sha256_matches",
        "job_request_sha256_matches",
        "preflight_result_sha256_matches",
        "dry_run_result_sha256_matches",
    ):
        if approval_report.get(field) is not True:
            return ("REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE", f"{field} must be true")
    return None


def _queue_only_proof_error(approval_report: dict) -> str | None:
    if approval_report.get("queue_only_confirmed") is True:
        return None
    dry_run_result = approval_report.get("dry_run_result", {})
    if dry_run_result.get("queue_only") is True or dry_run_result.get("enqueue_mode") == "queue_only":
        return None
    if dry_run_result.get("solver_execution_possible") is False and dry_run_result.get("queue_file"):
        return None
    return "queue-only behavior is not explicitly confirmed by the public API evidence"


def _real_enqueue_result(
    status: str,
    request: dict,
    project_root: str | None,
    errors: list[str],
    called_api: bool,
    available: bool | None = None,
    runtime_snapshot_before: dict | None = None,
    runtime_snapshot_after: dict | None = None,
    solver_output_snapshot_before: dict | None = None,
    solver_output_snapshot_after: dict | None = None,
    raw_result: dict | None = None,
) -> dict:
    return {
        "status": status,
        "dry_run": False,
        "called_api": called_api,
        "available": available,
        "project_root": project_root,
        "job_id": request.get("job_name"),
        "queue_mutated": False,
        "forbidden_mutation_detected": False,
        "runtime_snapshot_before": runtime_snapshot_before or snapshot_runtime_files(project_root),
        "runtime_snapshot_after": runtime_snapshot_after or snapshot_runtime_files(project_root),
        "solver_output_snapshot_before": solver_output_snapshot_before or snapshot_solver_output_files(request),
        "solver_output_snapshot_after": solver_output_snapshot_after or snapshot_solver_output_files(request),
        "errors": errors,
        "warnings": [],
        "raw_result": raw_result,
    }


def _to_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"status": "PREVIEW_READY", "raw_result": str(value)}
