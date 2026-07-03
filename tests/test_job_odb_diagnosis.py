from pathlib import Path

from abqpilot.diagnostics.job_odb_diagnosis import diagnose_job_output


def test_completed_job_with_odb_is_acceptable(tmp_path):
    _write(tmp_path, "job.sta", "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n")
    _write(tmp_path, "job.odb", "odb")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_COMPLETED_ODB_ACCEPTABLE"
    assert result["odb_acceptable_for_metrics"] is True


def test_odb_exists_but_analysis_not_completed_is_not_acceptable(tmp_path):
    _write(tmp_path, "job.sta", "THE ANALYSIS HAS NOT BEEN COMPLETED\n")
    _write(tmp_path, "job.msg", "***ERROR: THE ANALYSIS HAS BEEN TERMINATED DUE TO PREVIOUS ERRORS\n")
    _write(tmp_path, "job.odb", "partial")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_TERMINATED_BY_ERRORS"
    assert result["odb_acceptable_for_metrics"] is False


def test_too_many_attempts_maps_to_convergence_failed(tmp_path):
    _write(tmp_path, "job.msg", "***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT\n")
    _write(tmp_path, "job.sta", "THE ANALYSIS HAS NOT BEEN COMPLETED\n")
    _write(tmp_path, "job.odb", "partial")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_SOLVER_CONVERGENCE_FAILED"
    assert result["evidence"]["too_many_attempts"] is True


def test_input_processor_error_maps_to_input_failure(tmp_path):
    _write(tmp_path, "job.dat", "Analysis Input File Processor exited with an error\nUnknown node set\n")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_INPUT_PROCESSOR_FAILED"


def test_completion_without_odb_maps_to_missing_odb(tmp_path):
    _write(tmp_path, "job.sta", "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_COMPLETED_ODB_MISSING"
    assert result["odb_acceptable_for_metrics"] is False


def test_lock_exists_maps_to_running_or_stale(tmp_path):
    _write(tmp_path, "job.lck", "lock")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] in {"JOB_RUNNING_LOCK_ACTIVE", "JOB_LOCKED_STALE"}


def test_odb_without_completion_is_unproven(tmp_path):
    _write(tmp_path, "job.odb", "odb")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_ODB_EXISTS_BUT_COMPLETION_NOT_PROVEN"


def test_terminal_error_overrides_odb_existence(tmp_path):
    _write(tmp_path, "job.odb", "partial")
    _write(tmp_path, "job.msg", "***ERROR: THE ANALYSIS HAS BEEN TERMINATED DUE TO PREVIOUS ERRORS\n")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_TERMINATED_BY_ERRORS"
    assert result["odb_acceptable_for_metrics"] is False


def test_license_failure_maps_to_license_environment(tmp_path):
    _write(tmp_path, "job.log", "Abaqus Error: not enough licenses\n")

    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_LICENSE_OR_ENVIRONMENT_FAILED"


def test_unknown_evidence_is_unknown(tmp_path):
    result = diagnose_job_output(tmp_path, "job")

    assert result["diagnosis_status"] == "JOB_STATUS_UNKNOWN"


def test_diagnosis_never_opens_odb(tmp_path):
    _write(tmp_path, "job.odb", "not a real odb")

    result = diagnose_job_output(tmp_path, "job")

    assert result["safety_flags"]["opened_odb"] is False


def _write(root: Path, name: str, text: str) -> None:
    (root / name).write_text(text, encoding="utf-8")

