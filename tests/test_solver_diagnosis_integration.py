import json

from abqpilot.solver.solver_monitor import classify_solver_run
from abqpilot.solver.solver_report import intake_solver_run_output


def test_monitor_uses_diagnosis_result(tmp_path):
    _preflight(tmp_path)
    (tmp_path / "candidate_sanity_base_power_x2_stage4.odb").write_text("partial", encoding="utf-8")
    (tmp_path / "candidate_sanity_base_power_x2_stage4.msg").write_text(
        "***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT\n",
        encoding="utf-8",
    )
    (tmp_path / "candidate_sanity_base_power_x2_stage4.sta").write_text(
        "THE ANALYSIS HAS NOT BEEN COMPLETED\n",
        encoding="utf-8",
    )

    result = classify_solver_run(tmp_path)

    assert result["status"] == "SOLVER_FAILED"
    assert result["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"
    assert result["odb_acceptable_for_metrics"] is False


def test_intake_blocks_partial_failed_odb(tmp_path):
    _preflight(tmp_path)
    (tmp_path / "candidate_sanity_base_power_x2_stage4.odb").write_text("partial", encoding="utf-8")
    (tmp_path / "candidate_sanity_base_power_x2_stage4.msg").write_text("***ERROR: THE ANALYSIS HAS BEEN TERMINATED\n", encoding="utf-8")

    result = intake_solver_run_output(tmp_path)

    assert result["verdict"] == "SOLVER_OUTPUT_NOT_READY"
    assert result["details"]["odb_acceptable_for_metrics"] is False
    assert result["details"]["opened_odb"] is False


def _preflight(root):
    (root / "solver_preflight_result.json").write_text(
        json.dumps({"job_name": "candidate_sanity_base_power_x2_stage4"}),
        encoding="utf-8",
    )

