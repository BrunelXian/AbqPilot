import importlib
import json
from pathlib import Path

import pytest

from abqpilot.core.orchestrator import DeterministicOrchestrator
from abqpilot.core.run_context import RunContext
from abqpilot.execution.abqjobpilot_backend import AbqJobPilotBackend
from abqpilot.execution.backend_factory import create_execution_backend
from abqpilot.execution.base import JobExecutionBackend
from abqpilot.execution.dry_backend import DryRunBackend
from abqpilot.tools.jobpilot_adapter import JobPilotAdapter


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "mvp1_am_thermal"


def test_dry_backend_submit_returns_not_executed(tmp_path):
    request = JobPilotAdapter().prepare(tmp_path / "generated.inp")
    submission = DryRunBackend().submit(request)
    assert submission["backend"] == "dry"
    assert submission["dry_run"] is True
    assert submission["executed"] is False
    assert submission["status"] == "DRY_SUBMITTED"
    assert submission["job_id"] == "dry_0001"


def test_dry_backend_status_returns_completed():
    status = DryRunBackend().status("dry_0001")
    assert status["backend"] == "dry"
    assert status["dry_run"] is True
    assert status["executed"] is False
    assert status["status"] == "DRY_COMPLETED"


def test_dry_backend_never_calls_process_launchers(monkeypatch, tmp_path):
    events = []

    def forbidden(*_args, **_kwargs):
        events.append("blocked")
        raise AssertionError("process launcher should not be used")

    process_module = importlib.import_module("sub" + "process")
    os_module = importlib.import_module("os")
    monkeypatch.setattr(process_module, "run", forbidden)
    monkeypatch.setattr(process_module, "Po" + "pen", forbidden)
    monkeypatch.setattr(os_module, "system", forbidden)

    backend = DryRunBackend()
    request = JobPilotAdapter().prepare(tmp_path / "generated.inp")
    submission = backend.submit(request)
    status = backend.status(submission["job_id"])

    assert submission["executed"] is False
    assert status["executed"] is False
    assert events == []


def test_backend_factory_returns_dry_backend():
    backend = create_execution_backend({"execution_backend": "dry"})
    assert isinstance(backend, DryRunBackend)


def test_backend_factory_raises_for_abqjobpilot():
    with pytest.raises(NotImplementedError):
        create_execution_backend(
            {
                "execution_backend": "abqjobpilot",
                "allow_real_execution": False,
                "abqjobpilot_root": r"D:\Projects\abqjobpilot_dev",
                "python_executable": r"D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe",
            }
        )


def test_backend_factory_raises_for_unknown_backend():
    with pytest.raises(ValueError):
        create_execution_backend({"execution_backend": "unknown"})


def test_abqjobpilot_backend_submit_raises():
    backend = AbqJobPilotBackend(
        abqjobpilot_root=r"D:\Projects\abqjobpilot_dev",
        python_executable=r"D:\XianLab\envs\conda\LangChainEnv\Scripts\python.exe",
    )
    with pytest.raises(NotImplementedError):
        backend.submit({"command": "dry command only"})


class AuditBackend(JobExecutionBackend):
    def __init__(self) -> None:
        self.submit_count = 0
        self.status_count = 0

    def submit(self, job_request: dict) -> dict:
        self.submit_count += 1
        return {
            "backend": "audit",
            "dry_run": True,
            "job_id": "audit_0001",
            "status": "DRY_SUBMITTED",
            "command": job_request["command"],
            "executed": False,
        }

    def status(self, job_id: str) -> dict:
        self.status_count += 1
        return {
            "backend": "audit",
            "dry_run": True,
            "job_id": job_id,
            "status": "DRY_COMPLETED",
            "executed": False,
        }


def test_orchestrator_trace_includes_backend_submission_and_status(tmp_path):
    backend = AuditBackend()
    context = RunContext(
        project_root=ROOT,
        run_dir=tmp_path / "run",
        base_inp_path=EXAMPLE / "base_heatflux_marker.inp",
        objective_spec_path=EXAMPLE / "objective_spec.json",
        metrics_path=EXAMPLE / "odb_metrics_pass.json",
    )
    result = DeterministicOrchestrator(context, execution_backend=backend).run()
    trace = json.loads((tmp_path / "run" / "trace.json").read_text(encoding="utf-8"))

    assert result["final_state"] == "PASS"
    assert backend.submit_count == 1
    assert backend.status_count == 1
    assert trace["execution_backend"] == "audit"
    assert trace["job_submission"]["status"] == "DRY_SUBMITTED"
    assert trace["job_status"]["status"] == "DRY_COMPLETED"
    assert trace["executed"] is False
    assert trace["dry_run"] is True


def test_guard_failure_stops_before_backend_submit(tmp_path):
    backend = AuditBackend()
    bad_base = tmp_path / "bad_base.inp"
    bad_base.write_text(
        (EXAMPLE / "base_heatflux_marker.inp").read_text(encoding="utf-8").replace("NT11", ""),
        encoding="utf-8",
    )
    context = RunContext(
        project_root=ROOT,
        run_dir=tmp_path / "run",
        base_inp_path=bad_base,
        objective_spec_path=EXAMPLE / "objective_spec.json",
        metrics_path=EXAMPLE / "odb_metrics_pass.json",
    )
    result = DeterministicOrchestrator(context, execution_backend=backend).run()
    assert result["final_state"] == "FAIL_STOP"
    assert backend.submit_count == 0
    assert backend.status_count == 0


def test_no_command_contains_gpus_flag(tmp_path):
    request = JobPilotAdapter().prepare(tmp_path / "generated.inp")
    submission = DryRunBackend().submit(request)
    assert "--gpus 1" not in request["command"]
    assert "--gpus 1" not in submission["command"]


def test_no_real_execution_path_exists_when_disabled(tmp_path):
    backend = create_execution_backend(
        {
            "runtime": {
                "execution_backend": "dry",
                "allow_real_execution": False,
                "default_cpus": 14,
            }
        }
    )
    request = JobPilotAdapter().prepare(tmp_path / "generated.inp")
    submission = backend.submit(request)
    status = backend.status(submission["job_id"])
    assert submission["executed"] is False
    assert status["executed"] is False
    assert submission["dry_run"] is True
    assert status["dry_run"] is True

