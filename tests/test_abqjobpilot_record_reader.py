import json
import os
from pathlib import Path

from abqpilot.diagnostics.abqjobpilot_record_reader import (
    list_abqjobpilot_records,
    load_abqjobpilot_record_by_job_id,
    load_abqjobpilot_report,
    normalize_abqjobpilot_record,
)


def test_normalize_abqjobpilot_report_with_full_paths(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(
            {
                "job_id": "q1",
                "status": "FAILED_FATAL",
                "job_name": "job_a",
                "inp_path": str(tmp_path / "job_a.inp"),
                "work_dir": str(tmp_path),
                "sta_path": str(tmp_path / "job_a.sta"),
                "msg_path": str(tmp_path / "job_a.msg"),
                "dat_path": str(tmp_path / "job_a.dat"),
                "log_path": str(tmp_path / "job_a.log"),
                "odb_path": str(tmp_path / "job_a.odb"),
                "fatal_reason": "Abaqus Error",
                "return_code": 1,
            }
        ),
        encoding="utf-8",
    )

    record = load_abqjobpilot_report(report)

    assert record["record_source"] == "abqjobpilot"
    assert record["schema_version"] == "0.1"
    assert record["record_kind"] == "report"
    assert record["job_id"] == "q1"
    assert record["status"] == "FAILED_FATAL"
    assert record["dat_path"].endswith("job_a.dat")
    assert record["lck_path"].endswith("job_a.lck")
    assert record["lck_path_source"] == "derived_from_odb_path"


def test_normalize_report_with_missing_optional_fields(tmp_path):
    record = normalize_abqjobpilot_record({"job_id": "q2", "status": "QUEUED"}, tmp_path / "r.json")

    assert record["job_id"] == "q2"
    assert "job_name" in record["missing_fields"]
    assert record["raw_record"]["status"] == "QUEUED"


def test_derive_lck_path_from_job_name_and_work_dir_when_missing(tmp_path):
    record = normalize_abqjobpilot_record({"job_id": "q2b", "job_name": "job_c", "work_dir": str(tmp_path)})

    assert record["lck_path"] == str(tmp_path / "job_c.lck")
    assert record["lck_path_source"] == "derived_from_job_name_and_work_dir"


def test_load_queue_json_style_records(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "queue.json").write_text(
        json.dumps({"jobs": [{"job_id": "q3", "status": "QUEUED", "job_name": "job_b", "work_dir": str(tmp_path)}]}),
        encoding="utf-8",
    )

    records = list_abqjobpilot_records(runtime)

    assert records[0]["job_id"] == "q3"
    assert records[0]["job_name"] == "job_b"
    assert records[0]["record_kind"] == "queue"


def test_load_live_status_json_style_records(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "live_status.json").write_text(
        json.dumps({"job_id": "qlive", "status": "RUNNING", "job_name": "live_job"}),
        encoding="utf-8",
    )

    records = list_abqjobpilot_records(runtime)

    assert records[0]["job_id"] == "qlive"
    assert records[0]["record_kind"] == "live_status"


def test_list_records_filters_job_name_and_max_results(tmp_path):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "queue.json").write_text(
        json.dumps(
            {
                "jobs": [
                    {"job_id": "qa", "status": "FAILED_FATAL", "job_name": "alpha"},
                    {"job_id": "qb", "status": "FAILED_FATAL", "job_name": "beta"},
                    {"job_id": "qc", "status": "FAILED_FATAL", "job_name": "alpha_extra"},
                ]
            }
        ),
        encoding="utf-8",
    )

    records = list_abqjobpilot_records(runtime, status="FAILED_FATAL", job_name="alpha", max_results=1)

    assert len(records) == 1
    assert "alpha" in records[0]["job_name"]


def test_reports_directory_selects_newest_matching_job_id(tmp_path):
    runtime = tmp_path / "runtime"
    reports = runtime / "reports"
    reports.mkdir(parents=True)
    older = reports / "old.json"
    newer = reports / "new.json"
    older.write_text(json.dumps({"job_id": "q4", "status": "FAILED_FATAL", "job_name": "old"}), encoding="utf-8")
    newer.write_text(json.dumps({"job_id": "q4", "status": "COMPLETED", "job_name": "new"}), encoding="utf-8")
    os.utime(older, (1000, 1000))
    os.utime(newer, (2000, 2000))

    record = load_abqjobpilot_record_by_job_id("q4", runtime)

    assert record["job_id"] == "q4"
    assert record["job_name"] == "new"
    assert record["selection_reason"] == "newest_matching_report_by_mtime"
