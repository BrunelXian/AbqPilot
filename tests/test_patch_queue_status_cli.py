from abqpilot import cli


def test_parser_accepts_patched_job_commands():
    intake = cli.build_parser().parse_args(["intake-patched-job-output", "--workflow-dir", "workflow"])
    metrics = cli.build_parser().parse_args(["extract-patched-job-metrics", "--workflow-dir", "workflow"])
    report = cli.build_parser().parse_args(["report-patched-job", "--workflow-dir", "workflow"])

    assert intake.command == "intake-patched-job-output"
    assert metrics.command == "extract-patched-job-metrics"
    assert report.command == "report-patched-job"


def test_cli_intake_patched_job_output(tmp_path):
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    (workflow / "patch_candidate_manifest.json").write_text("{}", encoding="utf-8")
    (workflow / "patch_queue_status_summary.json").write_text(
        '{"normalized_status":"JOB_QUEUED","job_id":"q_patch","odb_exists":false,"lock_exists":false}',
        encoding="utf-8",
    )

    result = cli.command_intake_patched_job_output(workflow)

    assert result["verdict"] == "WAITING_FOR_PATCHED_JOB"
    assert result["details"]["submitted_solver"] is False


def test_cli_extract_patched_job_metrics_blocks_without_output(tmp_path):
    workflow = tmp_path / "workflow"
    workflow.mkdir()

    result = cli.command_extract_patched_job_metrics(workflow)

    assert result["verdict"] == "PATCHED_JOB_METRICS_BLOCKED_NO_ACCEPTED_OUTPUT"


def test_cli_report_patched_job_writes_report(tmp_path):
    workflow = tmp_path / "workflow"
    workflow.mkdir()
    (workflow / "patch_candidate_manifest.json").write_text("{}", encoding="utf-8")
    (workflow / "patch_queue_status_summary.json").write_text('{"normalized_status":"JOB_QUEUED"}', encoding="utf-8")
    (workflow / "patched_job_output_intake_summary.json").write_text("{}", encoding="utf-8")

    result = cli.command_report_patched_job(workflow)

    assert result["command"] == "report-patched-job"
    assert (workflow / "patched_job_report.json").exists()
