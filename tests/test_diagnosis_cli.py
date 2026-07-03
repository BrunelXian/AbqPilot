from abqpilot.cli import build_parser, command_diagnose_job_output


def test_diagnosis_cli_parser_exists():
    parser = build_parser()
    args = parser.parse_args(["diagnose-job-output", "--job-dir", ".", "--job-name", "job"])

    assert args.command == "diagnose-job-output"


def test_diagnosis_cli_writes_artifacts(tmp_path):
    (tmp_path / "job.sta").write_text("THE ANALYSIS HAS NOT BEEN COMPLETED\n", encoding="utf-8")
    (tmp_path / "job.msg").write_text("***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT\n", encoding="utf-8")
    (tmp_path / "job.odb").write_text("partial", encoding="utf-8")

    result = command_diagnose_job_output(tmp_path, "job")

    assert result["verdict"] == "JOB_SOLVER_CONVERGENCE_FAILED"
    assert (tmp_path / "job_odb_diagnosis_request.json").exists()
    assert (tmp_path / "job_odb_diagnosis_result.json").exists()
    assert (tmp_path / "job_odb_diagnosis_summary.md").exists()

