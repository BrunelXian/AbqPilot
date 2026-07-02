import json
from pathlib import Path

from abqpilot import cli
from abqpilot.core.pipeline_runner import PipelineRunner


def test_existing_completed_step_is_skipped_by_default(tmp_path):
    config_path = _write_config(tmp_path, existing_exported_inp_path=_write_sample_inp(tmp_path / "existing.inp"))
    runner = PipelineRunner(config_path=config_path, task_id="skip_completed")
    runner.run_until("01_export_cae")

    result = runner.run_step("01_export_cae")

    assert result["verdict"] == "SKIPPED_EXISTING_COMPLETED_STEP"
    assert runner.workspace.step_state("01_export_cae")["status"] == "COMPLETED"
    trace = _trace(runner)
    assert any(event["event"] == "STEP_SKIPPED" for event in trace)


def test_resume_continues_from_first_non_completed_step(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp, solver_search_root=tmp_path / "empty")
    runner = PipelineRunner(config_path=config_path, task_id="resume_next")
    runner.run_until("01_export_cae")

    resumed = PipelineRunner.open_existing(config_path=config_path, task_id="resume_next")
    result = resumed.resume()

    assert resumed.workspace.step_state("01_export_cae")["status"] == "COMPLETED"
    assert resumed.workspace.step_state("02_audit_heat_x2")["status"] == "COMPLETED"
    assert result["current_step"] == "08_solver_intake"


def test_resume_remains_waiting_if_manual_solver_outputs_missing(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp, solver_search_root=tmp_path / "empty")
    runner = PipelineRunner(config_path=config_path, task_id="resume_waiting")
    runner.run_until("08_solver_intake")

    resumed = PipelineRunner.open_existing(config_path=config_path, task_id="resume_waiting")
    result = resumed.resume()

    assert result["verdict"] == "NEED_MANUAL_SOLVER_OUTPUTS"
    assert result["final_status"] == "WAITING_FOR_MANUAL_SOLVER"
    assert result["requires_human_action"] is True


def test_resume_continues_if_manual_solver_outputs_later_exist(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    solver_root = tmp_path / "solver"
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp, solver_search_root=solver_root)
    runner = PipelineRunner(config_path=config_path, task_id="resume_after_outputs")
    runner.run_until("08_solver_intake")
    _write_solver_pair(solver_root)

    resumed = PipelineRunner.open_existing(config_path=config_path, task_id="resume_after_outputs")
    result = resumed.resume()

    assert resumed.workspace.step_state("08_solver_intake")["status"] == "COMPLETED"
    assert result["current_step"] in {"09_odb_metrics", "10_compare_metrics"}
    assert result["final_status"] != "WAITING_FOR_MANUAL_SOLVER"


def test_force_true_backs_up_old_step_directory_and_increments_rerun_count(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp)
    runner = PipelineRunner(config_path=config_path, task_id="force_backup")
    runner.run_until("02_audit_heat_x2")

    result = runner.run_step("02_audit_heat_x2", force=True)

    assert result["success"] is True
    assert (runner.workspace.steps_dir / "02_audit_heat_x2__rerun_backup_001").exists()
    assert runner.workspace.step_state("02_audit_heat_x2")["rerun_count"] == 1
    artifacts = runner.workspace.registry.to_dict()["artifacts"]
    assert any(item["kind"] == "backup" for item in artifacts)


def test_pipeline_trace_records_started_completed_and_failed(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp, solver_search_root=tmp_path / "empty")
    runner = PipelineRunner(config_path=config_path, task_id="trace_events")
    runner.run_until("08_solver_intake")

    events = [item["event"] for item in _trace(runner)]
    assert "STEP_STARTED" in events
    assert "STEP_COMPLETED" in events
    assert "PIPELINE_STOPPED" in events


def test_prepare_only_uses_stopped_by_mode_limit(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    _write_solver_pair(tmp_path / "solver")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp, solver_search_root=tmp_path / "solver")

    result = cli.command_run_sanity_demo(config_path, "prepare-only", task_id="mode_limit")

    assert result["verdict"] == "STOPPED_BY_MODE_LIMIT"
    assert result["final_status"] == "STOPPED_BY_MODE_LIMIT"
    assert result["stop_reason"] == "STOPPED_BY_MODE_LIMIT"


def test_missing_exported_inp_uses_need_exported_inp(tmp_path):
    config_path = _write_config(tmp_path)
    runner = PipelineRunner(config_path=config_path, task_id="need_inp")
    result = runner.run_until("02_audit_heat_x2")

    assert result["verdict"] == "NEED_EXPORTED_INP"
    assert result["stop_reason"] == "NEED_EXPORTED_INP"


def test_missing_odb_metrics_uses_need_odb_metrics_json(tmp_path):
    config_path = _write_config(tmp_path)
    runner = PipelineRunner(config_path=config_path, task_id="need_metrics")
    result = runner.run_step("10_compare_metrics")

    assert result["verdict"] == "NEED_ODB_METRICS_JSON"
    assert runner.workspace.state["stop_reason"] == "NEED_ODB_METRICS_JSON"


def test_cli_resume_routes_to_pipeline_runner_resume(monkeypatch, tmp_path):
    calls = []

    class FakeRunner:
        @classmethod
        def open_existing(cls, config_path, task_id, work_root=None, skip_completed=True):
            calls.append((config_path, task_id, work_root, skip_completed))
            return cls()

        def resume(self):
            return _fake_final()

    monkeypatch.setattr("abqpilot.core.pipeline_runner.PipelineRunner", FakeRunner)
    result = cli.command_run_sanity_demo(tmp_path / "config.json", task_id="demo", resume=True)

    assert calls
    assert result["task_id"] == "fake_task"


def test_cli_force_step_calls_forced_step_rerun(monkeypatch, tmp_path):
    calls = []

    class FakeRunner:
        def __init__(self, config_path, config=None, task_id=None, work_root=None, skip_completed=True):
            pass

        def run_step(self, step_name, force=False):
            calls.append((step_name, force))
            return {"command": step_name, "verdict": "PASS", "success": True, "output_paths": {}, "details": {}}

        def _finalize(self, result):
            final = _fake_final()
            final["verdict"] = result["verdict"]
            return final

    monkeypatch.setattr("abqpilot.core.pipeline_runner.PipelineRunner", FakeRunner)
    result = cli.command_run_sanity_demo(tmp_path / "config.json", task_id="demo", force_step="02_audit_heat_x2")

    assert calls == [("02_audit_heat_x2", True)]
    assert result["verdict"] == "PASS"


def _fake_final():
    return {
        "command": "run-sanity-demo",
        "verdict": "NEED_MANUAL_SOLVER_OUTPUTS",
        "success": False,
        "task_id": "fake_task",
        "task_dir": "fake_dir",
        "final_status": "WAITING_FOR_MANUAL_SOLVER",
        "current_step": "08_solver_intake",
        "stop_reason": "NEED_MANUAL_SOLVER_OUTPUTS",
        "requires_human_action": True,
        "human_action_reason": "Manual solver outputs are required before ODB metrics extraction.",
        "output_paths": {"task_state_json": "task_state.json"},
        "details": {},
    }


def _trace(runner: PipelineRunner):
    return json.loads(runner.workspace.trace_path.read_text(encoding="utf-8"))["events"]


def _write_config(tmp_path, existing_exported_inp_path=None, solver_search_root=None):
    cae = tmp_path / "model.cae"
    cae.write_bytes(b"placeholder")
    config = {
        "task_name": "sanity_base_heat_input_x2",
        "cae_path": str(cae),
        "work_root": str(tmp_path),
        "existing_exported_inp_path": str(existing_exported_inp_path) if existing_exported_inp_path else None,
        "solver_search_root": str(solver_search_root) if solver_search_root else str(tmp_path / "solver_missing"),
        "abaqus_command": "disabled",
        "allow_cae_export": False,
        "cae_export_mode": "write_input_only",
        "allow_odb_read": False,
        "odb_read_mode": "disabled",
        "allow_solver_submit": False,
        "allow_abqjobpilot": False,
        "allow_abqjobpilot_preflight": False,
        "allow_abqjobpilot_dry_run_enqueue": False,
        "allow_llm": False,
        "allow_cae_modify": False,
        "heat_input_scale": 2.0,
    }
    path = tmp_path / "task.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def _write_sample_inp(path: Path) -> Path:
    text = """*Heading
*Material, name=MAT
*Elastic
1., 0.3
*Node
1, 0., 0., 0.
*Element, type=C3D8T
1, 1, 1, 1, 1, 1, 1, 1, 1
*Step, name=heat
*Coupled Temperature-displacement
0.05, 1.
*Dflux
set-1, BF, 1e+10
*Output, field
*Node Output
NT, RF, U
*Element Output, directions=YES
HFL, PEEQ, S
*End Step
"""
    path.write_text(text, encoding="utf-8")
    return path


def _write_solver_pair(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for stem in ("sanity_base_power_1x", "sanity_base_power_2x"):
        (root / f"{stem}.odb").write_bytes(b"placeholder")
        (root / f"{stem}.sta").write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8")
