import json

from abqpilot.cli import build_parser, main


def test_propose_solver_repair_cli_parser_exists():
    args = build_parser().parse_args(["propose-solver-repair", "--solver-run-dir", "."])

    assert args.command == "propose-solver-repair"


def test_cli_writes_repair_artifacts(tmp_path):
    diagnosis = {
        "diagnosis_status": "JOB_SOLVER_CONVERGENCE_FAILED",
        "failure_category": "solver_convergence_failure",
        "odb_acceptable_for_metrics": False,
        "evidence": {
            "analysis_completed": False,
            "analysis_not_completed": True,
            "too_many_attempts": True,
            "terminated_due_to_errors": True,
        },
        "important_lines": {"msg_error_lines": ["***ERROR"], "sta_tail": ["tail"]},
        "job_name": "job",
    }
    (tmp_path / "job_odb_diagnosis_result.json").write_text(json.dumps(diagnosis), encoding="utf-8")

    code = main(["propose-solver-repair", "--solver-run-dir", str(tmp_path)])

    assert code == 0
    out = tmp_path / "solver_failure_repair_proposal"
    assert (out / "solver_failure_repair_context.json").exists()
    assert (out / "solver_failure_repair_proposal.json").exists()
    assert (out / "solver_failure_repair_validation.json").exists()
    assert (out / "solver_failure_repair_summary.md").exists()

