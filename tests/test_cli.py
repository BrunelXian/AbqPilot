import importlib
import json
from pathlib import Path

from abqpilot import cli


def test_cli_help_parser_builds_help_text():
    help_text = cli.build_parser().format_help()
    assert "AbqPilot deterministic CLI task runner" in help_text
    assert "run-sanity-demo" in help_text


def test_run_sanity_demo_parser_accepts_abqjobpilot_root():
    args = cli.build_parser().parse_args(
        [
            "run-sanity-demo",
            "--config",
            "configs/sanity_demo_task.json",
            "--task-id",
            "demo",
            "--abqjobpilot-root",
            r"D:\Projects\abqjobpilot_dev",
        ]
    )
    assert args.abqjobpilot_root == r"D:\Projects\abqjobpilot_dev"


def test_run_sanity_demo_parser_accepts_skip_dry_run_enqueue():
    args = cli.build_parser().parse_args(
        [
            "run-sanity-demo",
            "--config",
            "configs/sanity_demo_task.json",
            "--task-id",
            "demo",
            "--skip-jobpilot-dry-run-enqueue",
        ]
    )
    assert args.skip_jobpilot_dry_run_enqueue is True


def test_approve_jobpilot_enqueue_parser_accepts_required_args():
    args = cli.build_parser().parse_args(
        [
            "approve-jobpilot-enqueue",
            "--task-dir",
            r"D:\Projects\AbqPilot-v2\runs\tasks\demo",
            "--approved-by",
            "human",
            "--approval-phrase",
            "I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK",
            "--expires-hours",
            "24",
        ]
    )
    assert args.command == "approve-jobpilot-enqueue"
    assert args.approved_by == "human"


def test_cli_parser_accepts_mega_sprint_commands():
    parser = cli.build_parser()

    continue_args = parser.parse_args(
        ["continue-from-job-output", "--task-dir", r"D:\Projects\AbqPilot-v2\runs\tasks\demo"]
    )
    repair_args = parser.parse_args(["generate-repair-plan", "--task-dir", r"D:\Projects\AbqPilot-v2\runs\tasks\demo"])
    report_args = parser.parse_args(["export-run-report", "--task-dir", r"D:\Projects\AbqPilot-v2\runs\tasks\demo"])
    freeze_args = parser.parse_args(["alpha-freeze", "--root", r"D:\Projects\AbqPilot-v2"])
    status_args = parser.parse_args(["export-project-status", "--root", r"D:\Projects\AbqPilot-v2"])
    gui_args = parser.parse_args(["gui"])

    assert continue_args.command == "continue-from-job-output"
    assert repair_args.command == "generate-repair-plan"
    assert report_args.command == "export-run-report"
    assert freeze_args.command == "alpha-freeze"
    assert status_args.command == "export-project-status"
    assert gui_args.command == "gui"


def test_status_command_works_with_no_side_effects(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = cli.command_status(config_path=None)
    assert result["verdict"] == "STATUS_OK"
    assert result["success"] is True
    assert list(tmp_path.iterdir()) == []


def test_export_cae_disabled_mode_does_not_execute_subprocess(monkeypatch, tmp_path):
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("process launcher must not be called")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", forbidden)
    cae = tmp_path / "model.cae"
    cae.write_bytes(b"placeholder")

    result = cli.command_export_cae(cae, tmp_path / "out", "model_export")

    assert result["verdict"] == "CAE_EXPORT_DISABLED"
    assert result["details"]["report"]["executed"] is False
    assert calls == []


def test_audit_heat_x2_works_on_fixture_inp(tmp_path):
    source = _write_sample_inp(tmp_path / "source.inp")
    result = cli.command_audit_heat_x2(source, tmp_path / "audit", 2.0)
    assert result["success"] is True
    assert result["details"]["heat_input_keyword"] == "*Dflux"
    assert result["details"]["original_magnitude"] == 10000000000.0
    assert result["details"]["modified_magnitude"] == 20000000000.0
    assert Path(result["output_paths"]["generated_power_x2"]).exists()


def test_intake_solver_fails_closed_if_pair_missing(tmp_path):
    result = cli.command_intake_solver(tmp_path / "empty", tmp_path / "out")
    assert result["verdict"] == "FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND"
    assert result["success"] is False


def test_compare_metrics_works_on_fixture_metrics_json(tmp_path):
    metrics = _write_metrics_json(tmp_path / "metrics.json")
    result = cli.command_compare_metrics(metrics, tmp_path / "compare")
    assert result["success"] is True
    assert result["details"]["key_ratios"]["NT_max"] == 2.0
    assert result["details"]["key_ratios"]["S_Mises_max"] == 0.8
    assert Path(result["output_paths"]["comparison_report_json"]).exists()
    assert Path(result["output_paths"]["agent_observation_json"]).exists()


def test_run_sanity_demo_prepare_only_does_not_execute_subprocess(monkeypatch, tmp_path):
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("process launcher must not be called")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", forbidden)
    cae = tmp_path / "sanity.cae"
    cae.write_bytes(b"placeholder")
    config = tmp_path / "task.json"
    config.write_text(
        json.dumps(
            {
                "task_name": "prepare_only",
                "cae_path": str(cae),
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
                "allow_llm": False,
                "allow_cae_modify": False,
                "heat_input_scale": 2.0,
            }
        ),
        encoding="utf-8",
    )

    result = cli.command_run_sanity_demo(config, "prepare-only")

    assert result["verdict"] == "NEED_EXPORTED_INP"
    assert calls == []
    assert Path(result["output_paths"]["task_state_json"]).exists()


def test_cli_never_imports_or_calls_llm_modules():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    assert "abqpilot.llm_nodes" not in source
    assert "goal_compiler" not in source
    assert "eval_repair_agent" not in source


def test_cli_adds_no_new_process_launcher_paths():
    source = Path(cli.__file__).read_text(encoding="utf-8")
    forbidden = ["sub" + "process", "Po" + "pen", "os." + "system", "shell=True"]
    assert not any(token in source for token in forbidden)


def test_cli_main_status_returns_zero(tmp_path):
    result_path = tmp_path / "status.json"
    code = cli.main(["status", "--result-json", str(result_path)])
    assert code == 0
    saved = json.loads(result_path.read_text(encoding="utf-8"))
    assert saved["verdict"] == "STATUS_OK"


def test_run_sanity_demo_prints_dry_run_status(capsys):
    result = {
        "command": "run-sanity-demo",
        "verdict": "STOPPED_BY_MODE_LIMIT",
        "success": True,
        "task_id": "demo",
        "task_dir": "task",
        "final_status": "STOPPED_BY_MODE_LIMIT",
        "current_step": "08_solver_intake",
        "stop_reason": "STOPPED_BY_MODE_LIMIT",
        "requires_human_action": False,
        "human_action_reason": None,
        "abqjobpilot_project_root": r"D:\Projects\abqjobpilot_dev",
        "abqjobpilot_available": True,
        "abqjobpilot_preflight_status": "PREVIEW_READY",
        "abqjobpilot_command_preview_path": "preview.md",
        "abqjobpilot_dry_run_enqueue_status": "DRY_RUN_READY",
        "abqjobpilot_dry_run_result_path": "dry.json",
        "abqjobpilot_runtime_mutation_detected": False,
        "output_paths": {"task_state_json": "task_state.json"},
        "details": {},
    }

    cli._print_result(result)

    output = capsys.readouterr().out
    assert "abqjobpilot_dry_run_enqueue_status=DRY_RUN_READY" in output
    assert "abqjobpilot_runtime_mutation_detected=False" in output


def test_no_default_cli_path_uses_global_process_launchers(monkeypatch, tmp_path):
    events = []

    def forbidden(*_args, **_kwargs):
        events.append("blocked")
        raise AssertionError("process launcher should not be used")

    process_module = importlib.import_module("sub" + "process")
    os_module = importlib.import_module("os")
    monkeypatch.setattr(process_module, "run", forbidden)
    monkeypatch.setattr(process_module, "Po" + "pen", forbidden)
    monkeypatch.setattr(os_module, "system", forbidden)

    cae = tmp_path / "model.cae"
    cae.write_bytes(b"placeholder")
    result = cli.command_export_cae(cae, tmp_path / "out", "model_export")

    assert result["verdict"] == "CAE_EXPORT_DISABLED"
    assert events == []


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


def _write_metrics_json(path: Path) -> Path:
    payload = {
        "cases": [
            {
                "case_id": "base_power_1x",
                "role": "base",
                "status": "METRICS_EXTRACTED",
                "last_step": "Step_cool_00",
                "last_frame_time": 100.0,
                "temperature_field_used": "NT11",
                "metrics": {
                    "NT_max": 10.0,
                    "NT_mean_global": 4.0,
                    "S_Mises_max": 100.0,
                    "S_Mises_mean_global": 50.0,
                },
                "missing_fields": [],
            },
            {
                "case_id": "power_x2",
                "role": "power_x2",
                "status": "METRICS_EXTRACTED",
                "last_step": "Step_cool_00",
                "last_frame_time": 100.0,
                "temperature_field_used": "NT11",
                "metrics": {
                    "NT_max": 20.0,
                    "NT_mean_global": 8.0,
                    "S_Mises_max": 80.0,
                    "S_Mises_mean_global": 40.0,
                },
                "missing_fields": [],
            },
        ]
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
