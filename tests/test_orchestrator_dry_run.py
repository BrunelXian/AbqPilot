from pathlib import Path

from abqpilot.core.orchestrator import DeterministicOrchestrator
from abqpilot.core.run_context import RunContext
from abqpilot.execution.base import JobExecutionBackend
from abqpilot.tools.jobpilot_adapter import JobPilotAdapter


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "mvp1_am_thermal"


def test_orchestrator_valid_dry_run_reaches_final_verdict(tmp_path):
    context = RunContext(
        project_root=ROOT,
        run_dir=tmp_path / "run",
        base_inp_path=EXAMPLE / "base_heatflux_marker.inp",
        objective_spec_path=EXAMPLE / "objective_spec.json",
        metrics_path=EXAMPLE / "odb_metrics_pass.json",
    )
    result = DeterministicOrchestrator(context).run()
    assert result["final_state"] == "PASS"
    assert "JOB_REQUEST_READY" in result["state_history"]
    assert (tmp_path / "run" / "trace.json").exists()


def test_orchestrator_guard_failure_stops_before_job_request(tmp_path):
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
    result = DeterministicOrchestrator(context).run()
    assert result["final_state"] == "FAIL_STOP"
    assert "JOB_REQUEST_READY" not in result["state_history"]


def test_job_request_builder_does_not_execute(tmp_path):
    request = JobPilotAdapter().prepare(tmp_path / "generated.inp")
    assert request["executed"] is False
    assert request["dry_run"] is True
    assert "--gpus 1" not in request["command"]
    assert "--cpus 14" in request["command"]


class RecordingBackend(JobExecutionBackend):
    def __init__(self) -> None:
        self.submitted_requests = []
        self.status_requests = []

    def submit(self, job_request: dict) -> dict:
        self.submitted_requests.append(job_request)
        return {
            "backend": "recording",
            "dry_run": True,
            "job_id": "recording_0001",
            "status": "DRY_SUBMITTED",
            "command": job_request["command"],
            "executed": False,
        }

    def status(self, job_id: str) -> dict:
        self.status_requests.append(job_id)
        return {
            "backend": "recording",
            "dry_run": True,
            "job_id": job_id,
            "status": "DRY_COMPLETED",
            "executed": False,
        }


def test_orchestrator_uses_backend_injection(tmp_path):
    backend = RecordingBackend()
    context = RunContext(
        project_root=ROOT,
        run_dir=tmp_path / "run",
        base_inp_path=EXAMPLE / "base_heatflux_marker.inp",
        objective_spec_path=EXAMPLE / "objective_spec.json",
        metrics_path=EXAMPLE / "odb_metrics_pass.json",
    )
    result = DeterministicOrchestrator(context, execution_backend=backend).run()
    assert result["final_state"] == "PASS"
    assert len(backend.submitted_requests) == 1
    assert backend.status_requests == ["recording_0001"]


def test_guard_failure_stops_before_backend_submit(tmp_path):
    backend = RecordingBackend()
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
    assert backend.submitted_requests == []
