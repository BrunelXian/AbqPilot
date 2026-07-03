import json
from pathlib import Path

from abqpilot.core.hash_utils import sha256_file
from abqpilot.solver.dflux_guarded_solver_run import (
    DFLUX_APPROVAL_PHRASE,
    approve_dflux_guarded_solver_run,
    prepare_dflux_guarded_solver_run,
    run_dflux_guarded_solver_approved,
    validate_dflux_approval_token,
)


def test_dflux_guarded_eligibility_passes_when_validation_pass(tmp_path):
    preview, validation = _fixture(tmp_path)

    result = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")

    assert result["verdict"] == "DFLUX_GUARDED_SOLVER_RUN_PREPARED"
    details = result["details"]
    assert details["dflux_lifecycle_guard"] == "PASS"
    assert details["eligible_for_solver_after_human_approval"] is True
    assert details["solver_run_allowed_without_approval"] is False
    assert Path(details["solver_inp"]).read_text(encoding="utf-8") == preview.read_text(encoding="utf-8")
    assert sha256_file(preview) == details["preview_inp_sha256"]


def test_dflux_guard_blocks_missing_op_new(tmp_path):
    preview, validation = _fixture(tmp_path, cooling_step_has_dflux_op_new=False)

    result = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")

    assert result["verdict"] == "DFLUX_LIFECYCLE_GUARD_BLOCKED_SOLVER_RUN"
    assert result["details"]["eligible_for_solver_after_human_approval"] is False


def test_dflux_guard_blocks_positive_cooling_bf(tmp_path):
    preview, validation = _fixture(tmp_path, cooling_step_positive_bf_lines=1)

    result = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")

    assert result["verdict"] == "DFLUX_LIFECYCLE_GUARD_BLOCKED_SOLVER_RUN"


def test_dflux_guard_blocks_unrelated_changes(tmp_path):
    preview, validation = _fixture(tmp_path, unrelated_changes_count=2)

    result = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")

    assert result["verdict"] == "DFLUX_LIFECYCLE_GUARD_BLOCKED_SOLVER_RUN"


def test_dflux_guard_blocks_failed_validator(tmp_path):
    preview, validation = _fixture(tmp_path, static_validator="FAIL")

    result = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")

    assert result["verdict"] == "DFLUX_LIFECYCLE_GUARD_BLOCKED_SOLVER_RUN"


def test_dflux_approval_token_binds_hashes_and_command(tmp_path):
    preview, validation = _fixture(tmp_path)
    prepared = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")
    run_dir = Path(prepared["details"]["solver_run_dir"])

    approved = approve_dflux_guarded_solver_run(run_dir, DFLUX_APPROVAL_PHRASE)

    assert approved["verdict"] == "DFLUX_GUARDED_SOLVER_APPROVAL_TOKEN_CREATED"
    token = json.loads((run_dir / "approvals" / "dflux_guarded_solver_approval_token.json").read_text(encoding="utf-8"))
    assert token["preview_inp_sha256"] == sha256_file(preview)
    assert token["solver_inp_sha256"] == sha256_file(run_dir / "candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver.inp")
    assert token["dflux_lifecycle_validation_sha256"] == sha256_file(validation)
    assert token["cooling_step_has_dflux_op_new"] is True
    assert token["command_preview"][1] == "job=candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver"
    assert validate_dflux_approval_token(run_dir)["status"] == "APPROVAL_TOKEN_VALID"


def test_dflux_run_refuses_without_approval(tmp_path):
    preview, validation = _fixture(tmp_path)
    prepared = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")

    result = run_dflux_guarded_solver_approved(prepared["details"]["solver_run_dir"])

    assert result["verdict"] == "DFLUX_GUARDED_SOLVER_BLOCKED_APPROVAL_REQUIRED"
    assert result["details"]["solver_launched"] is False


def test_dflux_run_uses_narrow_runner_without_shell(monkeypatch, tmp_path):
    preview, validation = _fixture(tmp_path)
    prepared = prepare_dflux_guarded_solver_run(preview, validation, output_root=tmp_path / "runs", abaqus_command="abq.bat")
    run_dir = Path(prepared["details"]["solver_run_dir"])
    approve_dflux_guarded_solver_run(run_dir, DFLUX_APPROVAL_PHRASE)
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, cwd, capture_output, text, timeout, shell):
        calls.update({"command": command, "cwd": cwd, "shell": shell})
        root = Path(cwd)
        stem = "candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver"
        (root / f"{stem}.odb").write_text("odb", encoding="utf-8")
        (root / f"{stem}.sta").write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY", encoding="utf-8")
        return Completed()

    monkeypatch.setattr("abqpilot.solver.controlled_abaqus_runner.subprocess.run", fake_run)

    result = run_dflux_guarded_solver_approved(run_dir, timeout_s=7)

    assert result["verdict"] == "CONTROLLED_SOLVER_RUN_COMPLETED"
    assert calls["shell"] is False
    assert calls["command"][1:] == [
        "job=candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver",
        "input=candidate_sanity_base_power_x2_stage4_dflux_deactivated_solver.inp",
        "cpus=14",
        "interactive",
    ]


def _fixture(tmp_path, **overrides):
    preview = tmp_path / "preview.inp"
    preview.write_text("*Heading\n*Step, name=step_scan_00\n*Dflux\ninst_plate.set-body-1, BF, 2e+10\n*End Step\n*Step, name=Step_cool_00\n*Dflux, OP=NEW\n*End Step\n", encoding="utf-8")
    validation = {
        "static_validator": "PASS",
        "diff_guard": "PASS",
        "physics_guard": "PASS",
        "dflux_lifecycle_validator": "PASS",
        "source_inp_unchanged": True,
        "preview_inp_created": True,
        "cooling_step_has_dflux_op_new": True,
        "cooling_step_positive_bf_lines": 0,
        "scan_step_bf_preserved": True,
        "unrelated_changes_count": 0,
        **overrides,
    }
    path = tmp_path / "dflux_lifecycle_validation.json"
    path.write_text(json.dumps(validation), encoding="utf-8")
    return preview, path
