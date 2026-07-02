import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from abqpilot import cli
from abqpilot.core.pipeline_runner import PipelineRunner
from abqpilot.integrations import AbqJobPilotPreflightAdapter, normalize_jobpilot_status


def test_adapter_poll_status_calls_only_public_status(monkeypatch):
    calls = {"status": 0, "locate_outputs": 0, "enqueue": 0}

    class FakeClient:
        def status(self, job_id=None, inp_path=None):
            calls["status"] += 1
            return {"status": "QUEUED", "job_id": job_id, "inp_path": inp_path, "errors": [], "warnings": []}

        def locate_outputs(self, *_args, **_kwargs):
            calls["locate_outputs"] += 1
            raise AssertionError("locate_outputs must not be called by poll_status")

        def enqueue(self, *_args, **_kwargs):
            calls["enqueue"] += 1
            raise AssertionError("enqueue must not be called")

    monkeypatch.setattr(
        "abqpilot.integrations.abqjobpilot_adapter.importlib.import_module",
        lambda _name: SimpleNamespace(AbqJobPilotClient=FakeClient),
    )

    result = AbqJobPilotPreflightAdapter().poll_status(job_id="q_test")

    assert result["status"] == "QUEUED"
    assert calls == {"status": 1, "locate_outputs": 0, "enqueue": 0}


def test_adapter_locate_outputs_calls_only_public_locator(monkeypatch):
    calls = {"status": 0, "locate_outputs": 0, "enqueue": 0}

    class FakeClient:
        def status(self, *_args, **_kwargs):
            calls["status"] += 1
            raise AssertionError("status must not be called by locate_outputs")

        def locate_outputs(self, job_id=None, inp_path=None):
            calls["locate_outputs"] += 1
            return {
                "job_id": job_id,
                "inp_path": inp_path,
                "expected_odb_path": "case.odb",
                "odb_exists": False,
                "lock_exists": False,
                "errors": [],
                "warnings": [],
            }

        def enqueue(self, *_args, **_kwargs):
            calls["enqueue"] += 1
            raise AssertionError("enqueue must not be called")

    monkeypatch.setattr(
        "abqpilot.integrations.abqjobpilot_adapter.importlib.import_module",
        lambda _name: SimpleNamespace(AbqJobPilotClient=FakeClient),
    )

    result = AbqJobPilotPreflightAdapter().locate_outputs(job_id="q_test")

    assert result["expected_odb_path"] == "case.odb"
    assert calls == {"status": 0, "locate_outputs": 1, "enqueue": 0}


def test_status_poll_unavailable_when_import_fails(monkeypatch):
    monkeypatch.setattr(
        "abqpilot.integrations.abqjobpilot_adapter.importlib.import_module",
        lambda _name: (_ for _ in ()).throw(ImportError("missing")),
    )

    result = AbqJobPilotPreflightAdapter().poll_status(job_id="q_test")

    assert result["status"] == "ABQJOBPILOT_UNAVAILABLE"
    assert result["normalized_status"] == "ABQJOBPILOT_UNAVAILABLE"


@pytest.mark.parametrize(
    ("raw_status", "odb_exists", "lock_exists", "expected"),
    [
        ("QUEUED", False, False, "JOB_QUEUED"),
        ("RUNNING", False, False, "JOB_RUNNING"),
        ("COMPLETED", True, False, "JOB_OUTPUTS_READY"),
        ("COMPLETED", False, False, "JOB_ODB_MISSING"),
        ("FAILED", False, False, "JOB_FAILED"),
        ("LOCKED", False, True, "JOB_LOCKED"),
        ("UNKNOWN", False, False, "JOB_UNKNOWN"),
    ],
)
def test_normalize_jobpilot_status(raw_status, odb_exists, lock_exists, expected):
    assert (
        normalize_jobpilot_status(
            {"status": raw_status, "lock_exists": lock_exists},
            {"odb_exists": odb_exists, "lock_exists": lock_exists},
        )
        == expected
    )


def test_status_artifacts_are_written(tmp_path):
    adapter = AbqJobPilotPreflightAdapter()
    paths = adapter.write_status_artifacts(
        {
            "task_id": "task",
            "status": "QUEUED",
            "job_id": "q_test",
            "status_sources": ["queue.json"],
            "last_log_lines": [],
            "errors": [],
            "warnings": [],
        },
        {
            "job_id": "q_test",
            "working_dir": str(tmp_path),
            "expected_odb_path": str(tmp_path / "case.odb"),
            "odb_exists": False,
            "lock_exists": False,
            "errors": [],
            "warnings": [],
        },
        str(tmp_path / "out"),
    )

    assert set(paths) == {
        "abqjobpilot_status_request",
        "abqjobpilot_status_result",
        "abqjobpilot_output_locator_result",
        "abqjobpilot_status_summary",
        "abqjobpilot_status_summary_md",
    }
    summary = json.loads(Path(paths["abqjobpilot_status_summary"]).read_text(encoding="utf-8"))
    assert summary["normalized_status"] == "JOB_QUEUED"
    assert summary["opened_odb"] is False
    assert "No ODB was opened" in Path(paths["abqjobpilot_status_summary_md"]).read_text(encoding="utf-8")


def test_pipeline_status_poll_missing_job_id_returns_need_job_id(tmp_path):
    config_path = _write_config(tmp_path, poll=True)
    runner = PipelineRunner(config_path=config_path, task_id="missing_job_id")

    result = runner.run_step("07_abqjobpilot_status_poll")

    assert result["verdict"] == "NEED_ABQJOBPILOT_JOB_ID"


def test_pipeline_status_poll_records_artifacts(monkeypatch, tmp_path):
    config_path = _write_config(tmp_path, poll=True)
    runner = PipelineRunner(config_path=config_path, task_id="status_artifacts")
    real_result = runner.workspace.step_dir("06_abqjobpilot_real_enqueue") / "abqjobpilot_real_enqueue_result.json"
    real_result.parent.mkdir(parents=True, exist_ok=True)
    real_result.write_text(json.dumps({"status": "REAL_ENQUEUE_COMPLETED", "job_id": "q_test"}), encoding="utf-8")
    runner.workspace.registry.add_artifact("abqjobpilot_real_enqueue_result", "generated", real_result, "06_abqjobpilot_real_enqueue")
    runner.workspace.save_artifacts()

    class FakeAdapter:
        def __init__(self, project_root=None):
            pass

        def poll_status(self, job_id=None, inp_path=None):
            return {"task_id": "status_artifacts", "status": "QUEUED", "job_id": job_id, "errors": [], "warnings": []}

        def locate_outputs(self, job_id=None, inp_path=None):
            return {
                "job_id": job_id,
                "working_dir": str(tmp_path),
                "expected_odb_path": str(tmp_path / "case.odb"),
                "odb_exists": False,
                "lock_exists": False,
                "errors": [],
                "warnings": [],
            }

        def write_status_artifacts(self, status_result, output_result, out_dir):
            return AbqJobPilotPreflightAdapter().write_status_artifacts(status_result, output_result, out_dir)

    monkeypatch.setattr("abqpilot.integrations.AbqJobPilotPreflightAdapter", FakeAdapter)

    result = runner.run_step("07_abqjobpilot_status_poll")

    assert result["verdict"] == "JOB_QUEUED"
    assert runner.workspace.registry.get_artifact("abqjobpilot_status_summary") is not None
    assert runner.workspace.registry.get_artifact("expected_odb") is not None


def test_cli_parser_accepts_status_poll_flags():
    args = cli.build_parser().parse_args(
        [
            "run-sanity-demo",
            "--config",
            "configs/sanity_demo_task.json",
            "--poll-jobpilot-status",
            "--jobpilot-job-id",
            "q_test",
        ]
    )

    assert args.poll_jobpilot_status is True
    assert args.jobpilot_job_id == "q_test"


def _write_config(tmp_path, poll=False):
    config = {
        "task_name": "status_poll",
        "cae_path": str(tmp_path / "missing.cae"),
        "work_root": str(tmp_path / "runs"),
        "abaqus_command": "disabled",
        "allow_cae_export": False,
        "cae_export_mode": "write_input_only",
        "allow_odb_read": False,
        "odb_read_mode": "disabled",
        "allow_solver_submit": False,
        "allow_abqjobpilot": False,
        "allow_abqjobpilot_preflight": False,
        "allow_abqjobpilot_dry_run_enqueue": False,
        "allow_jobpilot_enqueue_authorization": False,
        "allow_abqjobpilot_real_enqueue": False,
        "allow_abqjobpilot_status_poll": True,
        "allow_llm": False,
        "allow_cae_modify": False,
        "heat_input_scale": 2.0,
        "poll_jobpilot_status": poll,
        "abqjobpilot": {"project_root": str(tmp_path / "missing"), "status_poll_enabled": True},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path
