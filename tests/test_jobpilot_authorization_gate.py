import json
from pathlib import Path

from abqpilot import cli
from abqpilot.core.approval import APPROVAL_PHRASE
from abqpilot.core.pipeline_runner import PipelineRunner
from abqpilot.core.pipeline_steps import STEP_NAMES


def test_pipeline_includes_jobpilot_authorization_step():
    assert "05_jobpilot_enqueue_authorization" in STEP_NAMES


def test_authorization_step_returns_approval_required_without_token(tmp_path):
    runner = _runner_with_authorization_evidence(tmp_path, "approval_required")

    result = runner.run_step("05_jobpilot_enqueue_authorization")

    assert result["verdict"] == "APPROVAL_REQUIRED"
    assert result["success"] is True
    assert Path(result["output_paths"]["jobpilot_enqueue_approval_request"]).exists()
    assert runner.workspace.registry.get_artifact("jobpilot_enqueue_approval_token") is None


def test_approval_token_is_not_created_automatically_by_pipeline(tmp_path):
    runner = _runner_with_authorization_evidence(tmp_path, "no_auto_token")

    runner.run_step("05_jobpilot_enqueue_authorization")

    assert not (runner.workspace.task_dir / "approvals" / "jobpilot_enqueue_approval_token.json").exists()


def test_authorization_step_returns_token_valid_with_valid_token(tmp_path):
    runner = _runner_with_authorization_evidence(tmp_path, "token_valid")
    runner.run_step("05_jobpilot_enqueue_authorization")
    cli.command_approve_jobpilot_enqueue(runner.workspace.task_dir, "human", APPROVAL_PHRASE, 24)

    result = runner.run_step("05_jobpilot_enqueue_authorization")

    assert result["verdict"] == "APPROVAL_TOKEN_VALID"
    assert result["success"] is True
    assert Path(result["output_paths"]["jobpilot_enqueue_approval_token"]).exists()


def test_stage_2_5_authorization_code_does_not_call_enqueue_or_solver_submit():
    approval_source = Path("abqpilot/core/approval.py").read_text(encoding="utf-8")
    step_source = Path("abqpilot/core/pipeline_steps.py").read_text(encoding="utf-8")

    assert "enqueue(" not in approval_source
    assert "submit(" not in approval_source
    authorization_segment = step_source.split("def step_jobpilot_enqueue_authorization", 1)[1].split(
        "def step_abqjobpilot_real_enqueue", 1
    )[0]
    assert "enqueue(" not in authorization_segment
    assert "submit(" not in authorization_segment


def _runner_with_authorization_evidence(tmp_path, task_id):
    config_path = _write_config(tmp_path)
    runner = PipelineRunner(config_path=config_path, task_id=task_id)
    evidence = runner.workspace.task_dir / "evidence"
    evidence.mkdir(parents=True)
    candidate = evidence / "generated_power_x2.inp"
    job_request = evidence / "abqjobpilot_job_request.json"
    preflight = evidence / "abqjobpilot_preflight_result.json"
    dry_run = evidence / "abqjobpilot_dry_run_enqueue_result.json"
    candidate.write_text("*Heading\n", encoding="utf-8")
    job_request.write_text(
        json.dumps(
            {
                "inp_path": str(candidate),
                "job_name": "generated_power_x2",
                "cpus": 14,
                "submission_mode": "preview_only",
                "allow_solver_submit": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    preflight.write_text(json.dumps({"status": "PREVIEW_READY"}, indent=2), encoding="utf-8")
    dry_run.write_text(
        json.dumps({"status": "DRY_RUN_READY", "runtime_mutation_detected": False}, indent=2),
        encoding="utf-8",
    )
    runner.workspace.registry.add_artifact("generated_power_x2", "generated", candidate, "02_audit_heat_x2")
    runner.workspace.registry.add_artifact("abqjobpilot_job_request", "generated", job_request, "03_abqjobpilot_preflight")
    runner.workspace.registry.add_artifact(
        "abqjobpilot_preflight_result", "generated", preflight, "03_abqjobpilot_preflight"
    )
    runner.workspace.registry.add_artifact(
        "abqjobpilot_dry_run_enqueue_result", "generated", dry_run, "04_abqjobpilot_dry_run_enqueue"
    )
    runner.workspace.save_artifacts()
    return runner


def _write_config(tmp_path):
    cae = tmp_path / "model.cae"
    cae.write_bytes(b"placeholder")
    config = {
        "task_name": "authorization_gate",
        "cae_path": str(cae),
        "work_root": str(tmp_path),
        "abaqus_command": "disabled",
        "allow_cae_export": False,
        "cae_export_mode": "write_input_only",
        "allow_odb_read": False,
        "odb_read_mode": "disabled",
        "allow_solver_submit": False,
        "allow_abqjobpilot": False,
        "allow_abqjobpilot_preflight": True,
        "allow_abqjobpilot_dry_run_enqueue": True,
        "allow_jobpilot_enqueue_authorization": True,
        "allow_abqjobpilot_real_enqueue": False,
        "allow_llm": False,
        "allow_cae_modify": False,
        "heat_input_scale": 2.0,
    }
    path = tmp_path / "task.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path
