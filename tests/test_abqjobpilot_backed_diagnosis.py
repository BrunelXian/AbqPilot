import json
from pathlib import Path

from abqpilot.diagnostics import diagnose_abqjobpilot_record
from abqpilot.diagnostics.abqjobpilot_record_reader import load_abqjobpilot_record_by_job_id


def _record(tmp_path: Path, status: str = "FAILED_FATAL") -> dict:
    job = tmp_path / "job"
    job.mkdir()
    return {
        "record_source": "abqjobpilot",
        "record_path": str(tmp_path / "report.json"),
        "job_id": "qdiag",
        "status": status,
        "raw_status": status,
        "job_name": "case",
        "work_dir": str(job),
        "dat_path": str(job / "case.dat"),
        "msg_path": str(job / "case.msg"),
        "sta_path": str(job / "case.sta"),
        "log_path": str(job / "case.log"),
        "odb_path": str(job / "case.odb"),
        "fatal_reason": "Abaqus Error",
        "return_code": 1,
        "raw_record": {},
    }


def test_diagnose_from_abqjobpilot_report_paths_maps_convergence(tmp_path):
    record = _record(tmp_path)
    Path(record["dat_path"]).write_text(
        "THE ANALYSIS HAS NOT BEEN COMPLETED\n***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT\n",
        encoding="utf-8",
    )
    Path(record["odb_path"]).write_bytes(b"partial")

    result = diagnose_abqjobpilot_record(record, artifact_dir=tmp_path / "diag")

    assert result["diagnosis_input_mode"] == "abqjobpilot_record"
    assert result["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"
    assert result["odb_acceptable_for_metrics"] is False
    assert result["abqjobpilot_record"]["job_id"] == "qdiag"


def test_completed_status_without_completion_logs_does_not_accept_odb(tmp_path):
    record = _record(tmp_path, status="COMPLETED")
    Path(record["odb_path"]).write_bytes(b"odb")

    result = diagnose_abqjobpilot_record(record, artifact_dir=tmp_path / "diag")

    assert result["diagnosis_status"] == "JOB_ODB_EXISTS_BUT_COMPLETION_NOT_PROVEN"
    assert result["odb_acceptable_for_metrics"] is False


def test_completed_status_with_completion_logs_and_odb_is_acceptable(tmp_path):
    record = _record(tmp_path, status="COMPLETED")
    Path(record["dat_path"]).write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8")
    Path(record["odb_path"]).write_bytes(b"odb")

    result = diagnose_abqjobpilot_record(record, artifact_dir=tmp_path / "diag")

    assert result["diagnosis_status"] == "JOB_COMPLETED_ODB_ACCEPTABLE"
    assert result["odb_acceptable_for_metrics"] is True


def test_attempt_block_parser_ignores_older_failure_when_latest_completed(tmp_path):
    record = _record(tmp_path, status="COMPLETED")
    Path(record["dat_path"]).write_text(
        "\n".join(
            [
                "START SOLVER_RUNNING",
                "THE ANALYSIS HAS NOT BEEN COMPLETED",
                "***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT",
                "END SOLVER_RUNNING",
                "START SOLVER_RUNNING",
                "THE ANALYSIS HAS COMPLETED SUCCESSFULLY",
                "END SOLVER_RUNNING",
            ]
        ),
        encoding="utf-8",
    )
    Path(record["odb_path"]).write_bytes(b"odb")

    result = diagnose_abqjobpilot_record(record, artifact_dir=tmp_path / "diag")

    assert result["diagnosis_status"] == "JOB_COMPLETED_ODB_ACCEPTABLE"
    assert result["evidence"]["too_many_attempts"] is False
    assert result["parser_mode"] == "latest_attempt_block"


def test_attempt_block_parser_keeps_latest_failure(tmp_path):
    record = _record(tmp_path, status="FAILED_FATAL")
    Path(record["dat_path"]).write_text(
        "\n".join(
            [
                "START SOLVER_RUNNING",
                "THE ANALYSIS HAS COMPLETED SUCCESSFULLY",
                "END SOLVER_RUNNING",
                "START SOLVER_RUNNING",
                "THE ANALYSIS HAS NOT BEEN COMPLETED",
                "***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT",
                "END SOLVER_RUNNING",
            ]
        ),
        encoding="utf-8",
    )
    Path(record["odb_path"]).write_bytes(b"partial")

    result = diagnose_abqjobpilot_record(record, artifact_dir=tmp_path / "diag")

    assert result["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"
    assert result["odb_acceptable_for_metrics"] is False
    assert result["parser_mode"] == "latest_attempt_block"


def test_diagnose_from_job_id_and_runtime_dir(tmp_path):
    runtime = tmp_path / "runtime"
    reports = runtime / "reports"
    reports.mkdir(parents=True)
    record = _record(tmp_path, status="FAILED_FATAL")
    Path(record["dat_path"]).write_text("***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT", encoding="utf-8")
    (reports / "qdiag.json").write_text(json.dumps(record), encoding="utf-8")

    loaded = load_abqjobpilot_record_by_job_id("qdiag", runtime)
    result = diagnose_abqjobpilot_record(loaded, artifact_dir=tmp_path / "diag")

    assert loaded["job_id"] == "qdiag"
    assert result["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"
