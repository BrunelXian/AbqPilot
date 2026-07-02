from __future__ import annotations

import json
from pathlib import Path

from abqpilot.builders.heat_flux_patch_builder import HeatFluxPatchBuilder
from abqpilot.core.run_context import RunContext
from abqpilot.core.state_machine import State, StateMachine
from abqpilot.execution.base import JobExecutionBackend
from abqpilot.execution.dry_backend import DryRunBackend
from abqpilot.tools.diff_guard_tool import DiffGuard
from abqpilot.tools.eval_repair_tool import EvalRepairTool
from abqpilot.tools.inventory_tool import InventoryTool
from abqpilot.tools.jobpilot_adapter import JobPilotAdapter
from abqpilot.tools.odb_extractor_tool import OdbExtractorTool
from abqpilot.tools.physics_guard_tool import PhysicsGuard
from abqpilot.tools.static_validator_tool import StaticValidator
from abqpilot.tools.trace_writer import TraceWriter


class DeterministicOrchestrator:
    def __init__(self, context: RunContext, execution_backend: JobExecutionBackend | None = None) -> None:
        self.context = context
        self.execution_backend = execution_backend or DryRunBackend()
        self.state_machine = StateMachine()
        self.trace_writer = TraceWriter(context.run_dir)

    def run(self) -> dict:
        ctx = self.context
        ctx.run_dir.mkdir(parents=True, exist_ok=True)

        objective_spec: dict = {}
        build_request: dict = {}
        build_status: dict = {}
        validation_report: dict = {}
        diff_report: dict = {}
        physics_guard_report: dict = {}
        job_request: dict = {}
        job_submission: dict = {}
        job_status: dict = {}
        odb_metrics: dict = {}
        evaluation: dict = {}
        repair_plan: dict = {}
        parameter_history: dict = {"iterations": []}

        try:
            self._advance(State.INPUT_READY, "input_ready", {"context": _context_payload(ctx)})

            inventory = InventoryTool().inspect(ctx.base_inp_path)
            if not inventory["ready"]:
                return self._fail_closed("inventory_not_ready", locals())
            self._advance(State.INVENTORY_READY, "inventory_ready", inventory)

            objective_spec = _read_json(ctx.objective_spec_path)
            self._advance(State.OBJECTIVE_READY, "objective_ready", objective_spec)

            scale = float(objective_spec.get("initial_parameters", {}).get("heat_flux_scale", 1.0))
            build_request = {
                "builder": "HeatFluxPatchBuilder",
                "base_inp_path": str(ctx.base_inp_path),
                "generated_inp_path": str(ctx.generated_inp_path),
                "parameters": {"heat_flux_scale": scale},
            }
            _write_json(ctx.build_request_path, build_request)
            self._advance(State.BUILD_REQUEST_READY, "build_request_ready", build_request)

            build_status = HeatFluxPatchBuilder().build(build_request)
            _write_json(ctx.run_dir / "build_status.json", build_status)
            if not build_status.get("allowed"):
                return self._fail_closed("build_failed", locals())
            self._advance(State.INP_GENERATED, "inp_generated", build_status)

            validation_report = StaticValidator().validate(
                ctx.generated_inp_path,
                target_region=objective_spec.get("target_region", "SURF_TRACK_001_TOP"),
            )
            _write_json(ctx.run_dir / "validation_report.json", validation_report)
            if not validation_report.get("passed"):
                self._advance(State.STATIC_VALIDATION_FAILED, "static_validation_failed", validation_report)
                return self._fail_closed("static_validation_failed", locals())
            self._advance(State.STATIC_VALIDATED, "static_validated", validation_report)

            diff_report = DiffGuard().compare(ctx.base_inp_path, ctx.generated_inp_path)
            _write_json(ctx.run_dir / "diff_report.json", diff_report)
            if not diff_report.get("allowed"):
                self._advance(State.DIFF_GUARD_FAILED, "diff_guard_failed", diff_report)
                return self._fail_closed("diff_guard_failed", locals())
            self._advance(State.DIFF_GUARD_PASSED, "diff_guard_passed", diff_report)

            physics_guard_report = PhysicsGuard().check(diff_report)
            _write_json(ctx.run_dir / "physics_guard_report.json", physics_guard_report)
            if not physics_guard_report.get("passed"):
                self._advance(State.PHYSICS_GUARD_FAILED, "physics_guard_failed", physics_guard_report)
                return self._fail_closed("physics_guard_failed", locals())
            self._advance(State.PHYSICS_GUARD_PASSED, "physics_guard_passed", physics_guard_report)

            job_request = JobPilotAdapter().prepare(ctx.generated_inp_path)
            _write_json(ctx.run_dir / "job_request.json", job_request)
            self._advance(State.JOB_REQUEST_READY, "job_request_ready", {"job_request": job_request})

            job_submission = self.execution_backend.submit(job_request)
            _write_json(ctx.run_dir / "job_submission.json", job_submission)
            self._advance(State.JOB_SUBMITTED, "job_submitted", job_submission)

            job_status = self.execution_backend.status(job_submission["job_id"])
            _write_json(ctx.run_dir / "job_status.json", job_status)
            self._advance(State.JOB_COMPLETED, "job_completed", job_status)

            if ctx.metrics_path is None:
                final_verdict = {
                    "final_state": "JOB_COMPLETED",
                    "verdict": "FINAL_DRY_RUN_COMPLETE",
                    "reason": "no fixture metrics supplied",
                }
                return self._finish(locals(), final_verdict)

            odb_metrics = OdbExtractorTool().extract(ctx.metrics_path)
            _write_json(ctx.run_dir / "odb_metrics.json", odb_metrics)
            if not odb_metrics.get("ok"):
                self._advance(State.ODB_MISSING, "odb_missing", odb_metrics)
                return self._fail_closed("fixture_metrics_missing", locals())
            self._advance(State.ODB_EXTRACTED, "odb_extracted", odb_metrics)
            self._advance(State.METRICS_READY, "metrics_ready", odb_metrics)

            evaluation, repair_plan = EvalRepairTool().evaluate(
                objective_spec, odb_metrics, parameter_history
            )
            _write_json(ctx.run_dir / "evaluation.json", evaluation)
            _write_json(ctx.run_dir / "repair_plan.json", repair_plan)
            if repair_plan.get("allowed"):
                parameter_history["iterations"].append(
                    {
                        "iteration": 1,
                        "parameters": {"heat_flux_scale": repair_plan["next_heat_flux_scale"]},
                        "source": "repair_plan",
                    }
                )
            _write_json(ctx.run_dir / "parameter_history.json", parameter_history)
            self._advance(State.EVALUATED, "evaluated", {"evaluation": evaluation, "repair_plan": repair_plan})

            final_state = State(evaluation.get("final_state", "FAIL_STOP"))
            self._advance(final_state, final_state.value.lower(), evaluation)
            final_verdict = {
                "final_state": final_state.value,
                "verdict": evaluation.get("result", final_state.value),
                "reason": repair_plan.get("reason"),
            }
            return self._finish(locals(), final_verdict)
        except Exception as exc:
            final_verdict = {
                "final_state": "FAIL_STOP",
                "verdict": "FAIL_STOP",
                "reason": f"exception: {exc}",
            }
            return self._finish(locals(), final_verdict)

    def _advance(self, next_state: State, step: str, payload: dict | None = None) -> None:
        state = self.state_machine.transition(next_state)
        self.trace_writer.record(step, state.value, payload)

    def _fail_closed(self, reason: str, local_values: dict) -> dict:
        if self.state_machine.current != State.FAIL_STOP:
            self._advance(State.FAIL_STOP, "fail_stop", {"reason": reason})
        final_verdict = {"final_state": "FAIL_STOP", "verdict": "FAIL_STOP", "reason": reason}
        return self._finish(local_values, final_verdict)

    def _finish(self, local_values: dict, final_verdict: dict) -> dict:
        trace_payload = _trace_payload(self.context, local_values, final_verdict, self.state_machine.history)
        trace_paths = self.trace_writer.write(trace_payload)
        _write_json(self.context.run_dir / "final_verdict.json", final_verdict)
        return {**final_verdict, "trace": trace_paths, "state_history": self.state_machine.history}


def _context_payload(ctx: RunContext) -> dict:
    return {
        "project_root": str(ctx.project_root),
        "run_dir": str(ctx.run_dir),
        "base_inp_path": str(ctx.base_inp_path),
        "objective_spec_path": str(ctx.objective_spec_path),
        "metrics_path": str(ctx.metrics_path) if ctx.metrics_path else None,
    }


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _trace_payload(ctx: RunContext, values: dict, final_verdict: dict, state_history: list[str]) -> dict:
    names = [
        "objective_spec",
        "build_request",
        "build_status",
        "validation_report",
        "diff_report",
        "physics_guard_report",
        "job_request",
        "job_submission",
        "job_status",
        "odb_metrics",
        "evaluation",
        "repair_plan",
        "parameter_history",
    ]
    payload = {
        "input_paths": _context_payload(ctx),
        "state_history": state_history,
        "final_verdict": final_verdict,
    }
    for name in names:
        payload[name] = values.get(name, {})
    payload["dry_job_command"] = payload.get("job_request", {}).get("command")
    payload["execution_backend"] = payload.get("job_submission", {}).get("backend")
    payload["executed"] = bool(
        payload.get("job_submission", {}).get("executed")
        or payload.get("job_status", {}).get("executed")
    )
    payload["dry_run"] = bool(
        payload.get("job_submission", {}).get("dry_run")
        or payload.get("job_status", {}).get("dry_run")
        or payload.get("job_request", {}).get("dry_run")
    )
    return payload
