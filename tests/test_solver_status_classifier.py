from pathlib import Path

from abqpilot.tools.solver_status_classifier import classify_solver_status


def test_classify_completed_text_as_completed(tmp_path):
    case = _case(tmp_path, "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n")
    report = classify_solver_status(case)
    assert report["status"] == "COMPLETED"


def test_classify_failed_text_as_failed(tmp_path):
    case = _case(tmp_path, "Abaqus/Analysis exited with errors\n")
    report = classify_solver_status(case)
    assert report["status"] == "FAILED"


def test_classify_mixed_success_error_as_unknown(tmp_path):
    case = _case(tmp_path, "COMPLETED SUCCESSFULLY\nERROR: later text\n")
    report = classify_solver_status(case)
    assert report["status"] == "UNKNOWN"


def test_classify_lock_as_running_or_locked(tmp_path):
    case = _case(tmp_path, "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n")
    lck = tmp_path / "job.lck"
    lck.write_text("", encoding="utf-8")
    case["lck_path"] = str(lck)
    case["lock_exists"] = True
    report = classify_solver_status(case)
    assert report["status"] == "RUNNING_OR_LOCKED"


def _case(tmp_path: Path, text: str) -> dict:
    sta = tmp_path / "job.sta"
    sta.write_text(text, encoding="utf-8")
    return {
        "case_id": "base_power_1x",
        "sta_path": str(sta),
        "msg_path": None,
        "dat_path": None,
        "log_path": None,
        "lock_exists": False,
    }

