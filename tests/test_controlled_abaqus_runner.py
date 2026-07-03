from pathlib import Path

from abqpilot.solver.solver_approval import SOLVER_APPROVAL_PHRASE, approve_solver_run
from abqpilot.solver.controlled_abaqus_runner import run_solver_approved
from abqpilot.solver.solver_preflight import prepare_solver_run
from tests.test_solver_preflight import _valid_candidate


def test_run_without_approval_blocks(tmp_path):
    run_dir = _prepared_run(tmp_path)

    result = run_solver_approved(run_dir)

    assert result["verdict"] == "CONTROLLED_SOLVER_RUN_BLOCKED_APPROVAL_REQUIRED"
    assert result["details"]["solver_launched"] is False


def test_runner_uses_fixed_subprocess_without_shell(monkeypatch, tmp_path):
    run_dir = Path(_prepared_run(tmp_path))
    approve_solver_run(run_dir, "human", SOLVER_APPROVAL_PHRASE)
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, cwd, capture_output, text, timeout, shell):
        calls.update(
            {
                "command": command,
                "cwd": cwd,
                "capture_output": capture_output,
                "text": text,
                "timeout": timeout,
                "shell": shell,
            }
        )
        (Path(cwd) / "candidate_sanity_base_power_x2_stage4.odb").write_text("odb", encoding="utf-8")
        (Path(cwd) / "candidate_sanity_base_power_x2_stage4.sta").write_text("THE ANALYSIS HAS COMPLETED", encoding="utf-8")
        return Completed()

    monkeypatch.setattr("abqpilot.solver.controlled_abaqus_runner.subprocess.run", fake_run)

    result = run_solver_approved(run_dir, run_dir / "approvals" / "solver_run_approval_token.json", timeout_s=12)

    assert result["verdict"] == "CONTROLLED_SOLVER_RUN_COMPLETED"
    assert calls["shell"] is False
    assert calls["command"][1:] == [
        "job=candidate_sanity_base_power_x2_stage4",
        "input=candidate_sanity_base_power_x2_stage4.inp",
        "cpus=14",
        "interactive",
    ]


def _prepared_run(tmp_path):
    candidate, source, evidence = _valid_candidate(tmp_path)
    result = prepare_solver_run(candidate, source, evidence, run_root=tmp_path / "runs", abaqus_command="abq.bat")
    return result["details"]["solver_run_dir"]
