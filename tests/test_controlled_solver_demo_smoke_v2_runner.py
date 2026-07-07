from pathlib import Path

import abqpilot.solver.stage5_3a_v2_demo_runner as runner


def _request(tmp_path: Path, inp: Path) -> dict:
    return {"solver_command_path": runner.ABAQUS_COMMAND, "candidate_inp_path": str(inp), "working_directory": str(tmp_path / "runs" / "tasks" / "stage5_3a_v2_controlled_solver_demo_smoke" / "artifacts" / "solver_work"), "timeout_seconds": 1, "task_id": runner.TASK_ID, "smoke_demo_only": True, "arbitrary_task_execution_allowed": False, "solver_execution_allowed": True, "executable_request": True}


def test_demo_smoke_v2_runner_builds_fixed_command_shape(tmp_path: Path) -> None:
    inp = (tmp_path / "demo_solver_smoke.inp").resolve()
    command = runner.build_stage5_3a_v2_demo_command(inp)
    assert isinstance(command, list)
    assert command[0] == r"D:\ABAQUS2024\Commands\abq2024.bat"
    assert f"input={inp}" in command
    assert "cpus=4" in command
    assert "interactive" in command


def test_demo_smoke_v2_runner_blocks_missing_abaqus(monkeypatch, tmp_path: Path) -> None:
    missing = str(tmp_path / "missing_abq2024.bat")
    monkeypatch.setattr(runner, "ABAQUS_COMMAND", missing)
    inp = tmp_path / "demo_solver_smoke.inp"
    inp.write_text("*Heading\n", encoding="utf-8")
    result = runner.execute_stage5_3a_v2_demo_solver_request(_request(tmp_path, inp))
    assert result["solver_status"] == "STAGE5_3A_V2_BLOCKED_ABAQUS_COMMAND_NOT_FOUND"
    assert result["solver_invoked"] is False
    assert result["shell"] is False
    assert result["command_is_list"] is True


def test_demo_smoke_v2_runner_rejects_arbitrary_command_and_task(tmp_path: Path) -> None:
    inp = tmp_path / "demo_solver_smoke.inp"
    inp.write_text("*Heading\n", encoding="utf-8")
    request = _request(tmp_path, inp)
    request["solver_command_path"] = str(tmp_path / "other.bat")
    assert runner.execute_stage5_3a_v2_demo_solver_request(request)["solver_status"] == "STAGE5_3A_V2_BLOCKED_UNSAFE_COMMAND_SHAPE"
    request = _request(tmp_path, inp)
    request["task_id"] = "other_task"
    assert runner.execute_stage5_3a_v2_demo_solver_request(request)["solver_status"] == "STAGE5_3A_V2_BLOCKED_ARBITRARY_TASK_PATH"
