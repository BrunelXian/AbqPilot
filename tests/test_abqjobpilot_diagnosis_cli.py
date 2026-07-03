import json
from pathlib import Path

from abqpilot import cli


def test_cli_parser_accepts_abqjobpilot_diagnosis_options():
    args = cli.build_parser().parse_args(
        [
            "diagnose-job-output",
            "--abqjobpilot-job-id",
            "q1",
            "--abqjobpilot-runtime-dir",
            "runtime",
        ]
    )

    assert args.command == "diagnose-job-output"
    assert args.abqjobpilot_job_id == "q1"


def test_cli_parser_accepts_list_filters():
    args = cli.build_parser().parse_args(
        [
            "list-abqjobpilot-records",
            "--abqjobpilot-runtime-dir",
            "runtime",
            "--status",
            "FAILED_FATAL",
            "--job-name",
            "case",
            "--max-results",
            "5",
        ]
    )

    assert args.status == "FAILED_FATAL"
    assert args.job_name == "case"
    assert args.max_results == 5


def test_cli_diagnose_from_abqjobpilot_report(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    (work / "case.dat").write_text("***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "job_id": "qcli",
                "status": "FAILED_FATAL",
                "job_name": "case",
                "work_dir": str(work),
                "dat_path": str(work / "case.dat"),
                "odb_path": str(work / "case.odb"),
            }
        ),
        encoding="utf-8",
    )

    result = cli.command_diagnose_job_output(abqjobpilot_report=report)

    assert result["details"]["diagnosis_input_mode"] == "abqjobpilot_record"
    assert result["details"]["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"


def test_list_command_is_read_only(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    queue = runtime / "queue.json"
    queue.write_text(json.dumps({"jobs": [{"job_id": "qread", "status": "QUEUED"}]}), encoding="utf-8")
    before = queue.read_text(encoding="utf-8")

    result = cli.command_list_abqjobpilot_records(runtime)

    assert result["details"]["record_count"] == 1
    assert queue.read_text(encoding="utf-8") == before
    assert result["details"]["mutated_runtime"] is False
