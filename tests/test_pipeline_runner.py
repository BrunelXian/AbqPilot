import json
from pathlib import Path

from abqpilot import cli
from abqpilot.core.pipeline_steps import STEP_NAMES
from abqpilot.core.pipeline_runner import PipelineRunner


def test_pipeline_stops_with_need_exported_inp_if_audit_lacks_inp(tmp_path):
    config_path = _write_config(tmp_path)
    runner = PipelineRunner(config_path=config_path, task_id="missing_inp")
    result = runner.run_until("02_audit_heat_x2")

    assert result["verdict"] == "NEED_EXPORTED_INP"
    assert result["final_status"] == "FAILED"
    assert (runner.workspace.step_result_path("02_audit_heat_x2")).exists()


def test_pipeline_stops_with_manual_solver_boundary(tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp, solver_search_root=tmp_path / "empty_solver")
    runner = PipelineRunner(config_path=config_path, task_id="manual_boundary")
    result = runner.run_until("08_solver_intake")

    assert result["verdict"] == "NEED_MANUAL_SOLVER_OUTPUTS"
    assert result["final_status"] == "WAITING_FOR_MANUAL_SOLVER"
    assert result["stop_reason"] == "NEED_MANUAL_SOLVER_OUTPUTS"
    assert result["requires_human_action"] is True
    assert result["human_action_reason"] == "Manual solver outputs are required before ODB metrics extraction."
    assert (runner.workspace.task_dir / "artifacts.json").exists()
    assert (runner.workspace.task_dir / "pipeline_trace.json").exists()
    assert (runner.workspace.task_dir / "final_result.json").exists()


def test_pipeline_does_not_submit_solver_or_call_llm(monkeypatch, tmp_path):
    events = []

    def forbidden(*_args, **_kwargs):
        events.append("called")
        raise AssertionError("process launcher must not be called")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", forbidden)
    config_path = _write_config(tmp_path)
    runner = PipelineRunner(config_path=config_path, task_id="no_submit")
    runner.run_until("02_audit_heat_x2")

    assert events == []
    source = Path("abqpilot/core/pipeline_runner.py").read_text(encoding="utf-8")
    assert "llm_nodes" not in source
    assert "submit(" not in source


def test_run_sanity_demo_prepare_only_uses_pipeline_runner(monkeypatch, tmp_path):
    calls = []

    class FakeRunner:
        def __init__(self, config_path, config=None, task_id=None, work_root=None, skip_completed=True):
            calls.append((config_path, config, task_id, work_root, skip_completed))

        def run_until(self, step_name, mode_limit=False):
            assert step_name == "08_solver_intake"
            assert mode_limit is True
            return _fake_final()

        def run_all(self):
            raise AssertionError("prepare-only should not run all")

    monkeypatch.setattr("abqpilot.core.pipeline_runner.PipelineRunner", FakeRunner)
    result = cli.command_run_sanity_demo(tmp_path / "config.json", "prepare-only", task_id="demo", work_root=tmp_path)

    assert calls
    assert result["task_id"] == "fake_task"


def test_existing_cli_status_still_works():
    result = cli.command_status(config_path=None)
    assert result["verdict"] == "STATUS_OK"


def test_pipeline_includes_abqjobpilot_preflight_step():
    assert "03_abqjobpilot_preflight" in STEP_NAMES


def test_pipeline_includes_abqjobpilot_dry_run_enqueue_step():
    assert "04_abqjobpilot_dry_run_enqueue" in STEP_NAMES


def test_pipeline_stops_if_jobpilot_preflight_lacks_candidate_inp(tmp_path):
    config_path = _write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["allow_abqjobpilot_preflight"] = True
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    runner = PipelineRunner(config_path=config_path, task_id="missing_jobpilot_candidate")

    result = runner.run_step("03_abqjobpilot_preflight")

    assert result["verdict"] == "NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT"
    assert runner.workspace.state["stop_reason"] == "NEED_CANDIDATE_INP_FOR_JOBPILOT_PREFLIGHT"


def test_skip_jobpilot_preflight_skips_safely(tmp_path):
    config_path = _write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["allow_abqjobpilot_preflight"] = True
    config["skip_jobpilot_preflight"] = True
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    runner = PipelineRunner(config_path=config_path, task_id="skip_jobpilot")

    result = runner.run_step("03_abqjobpilot_preflight")

    assert result["verdict"] == "SKIPPED_JOBPILOT_PREFLIGHT"
    assert result["success"] is True


def test_pipeline_stops_if_dry_run_enqueue_lacks_preflight_request(tmp_path):
    config_path = _write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["allow_abqjobpilot_dry_run_enqueue"] = True
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    runner = PipelineRunner(config_path=config_path, task_id="missing_dry_request")

    result = runner.run_step("04_abqjobpilot_dry_run_enqueue")

    assert result["verdict"] == "NEED_JOBPILOT_PREFLIGHT_REQUEST"
    assert runner.workspace.state["stop_reason"] == "NEED_JOBPILOT_PREFLIGHT_REQUEST"


def test_skip_jobpilot_dry_run_enqueue_skips_safely(tmp_path):
    config_path = _write_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["allow_abqjobpilot_dry_run_enqueue"] = True
    config["skip_jobpilot_dry_run_enqueue"] = True
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    runner = PipelineRunner(config_path=config_path, task_id="skip_dry_run")

    result = runner.run_step("04_abqjobpilot_dry_run_enqueue")

    assert result["verdict"] == "SKIPPED_JOBPILOT_DRY_RUN_ENQUEUE"
    assert result["success"] is True


def test_pipeline_passes_project_root_to_adapter(monkeypatch, tmp_path):
    source_inp = _write_sample_inp(tmp_path / "existing.inp")
    config_path = _write_config(tmp_path, existing_exported_inp_path=source_inp)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["allow_abqjobpilot_preflight"] = True
    config["abqjobpilot"] = {
        "project_root": str(tmp_path / "fake_root"),
        "cpus": 14,
        "batch": "batch",
        "strategy": "strategy",
        "submission_mode": "preview_only",
        "allow_solver_submit": False,
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    seen = []

    class FakeAdapter:
        def __init__(self, project_root=None):
            seen.append(project_root)

        def build_request(self, **kwargs):
            return {
                "inp_path": kwargs["inp_path"],
                "job_name": kwargs["job_name"],
                "cpus": kwargs["cpus"],
                "batch": kwargs["batch"],
                "strategy": kwargs["strategy"],
                "working_dir": kwargs["working_dir"],
                "submission_mode": "preview_only",
                "allow_solver_submit": False,
                "metadata": kwargs["metadata"],
            }

        def preflight(self, request):
            return {"status": "PREVIEW_READY", "errors": [], "warnings": [], "available": True, "project_root": seen[-1]}

        def write_preflight_artifacts(self, request, result, out_dir):
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            paths = {}
            for name in ("abqjobpilot_job_request", "abqjobpilot_preflight_result", "abqjobpilot_command_preview"):
                path = out / f"{name}.json"
                path.write_text(json.dumps(result), encoding="utf-8")
                paths[name] = str(path)
            return paths

        def diagnostics(self):
            return {"available": True, "project_root": seen[-1]}

    monkeypatch.setattr("abqpilot.integrations.AbqJobPilotPreflightAdapter", FakeAdapter)
    runner = PipelineRunner(config_path=config_path, task_id="project_root_passed")
    runner.run_until("03_abqjobpilot_preflight")

    assert seen == [str(tmp_path / "fake_root")]


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
