import json

from abqpilot.solver.solver_monitor import classify_solver_run


def test_monitor_maps_lck_to_running(tmp_path):
    run = _run(tmp_path)
    (run / "candidate_sanity_base_power_x2_stage4.lck").write_text("lock", encoding="utf-8")

    status = classify_solver_run(run)

    assert status["status"] == "SOLVER_RUNNING"


def test_monitor_maps_odb_completion_to_completed(tmp_path):
    run = _run(tmp_path)
    (run / "candidate_sanity_base_power_x2_stage4.odb").write_text("odb", encoding="utf-8")
    (run / "candidate_sanity_base_power_x2_stage4.sta").write_text("THE ANALYSIS HAS COMPLETED", encoding="utf-8")

    status = classify_solver_run(run)

    assert status["status"] == "SOLVER_COMPLETED"


def test_monitor_maps_dat_error_to_failed(tmp_path):
    run = _run(tmp_path)
    (run / "candidate_sanity_base_power_x2_stage4.dat").write_text("Abaqus Error: bad model", encoding="utf-8")

    status = classify_solver_run(run)

    assert status["status"] == "SOLVER_FAILED"


def _run(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "solver_preflight_result.json").write_text(
        json.dumps({"job_name": "candidate_sanity_base_power_x2_stage4"}),
        encoding="utf-8",
    )
    return run
