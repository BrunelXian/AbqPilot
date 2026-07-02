from pathlib import Path

from abqpilot.tools.solver_output_intake import inventory_solver_outputs


def test_detect_complete_pair_of_solver_output_files(tmp_path):
    _write_case(tmp_path, "sanity_base_power_1x")
    _write_case(tmp_path, "sanity_base_power_2x")
    report = inventory_solver_outputs([tmp_path])
    assert report["verdict"] == "SOLVER_OUTPUT_PAIR_FOUND"
    assert len(report["cases"]) == 2
    assert {case["expected_role"] for case in report["cases"]} == {"base", "power_x2"}
    assert all(case["odb_exists"] for case in report["cases"])


def test_fail_when_only_one_case_exists(tmp_path):
    _write_case(tmp_path, "sanity_base_power_1x")
    report = inventory_solver_outputs([tmp_path])
    assert report["verdict"] == "FAIL_SOLVER_OUTPUT_PAIR_NOT_FOUND"


def test_fail_when_no_odb_exists(tmp_path):
    _write_case(tmp_path, "sanity_base_power_1x", include_odb=False)
    _write_case(tmp_path, "sanity_base_power_2x", include_odb=False)
    report = inventory_solver_outputs([tmp_path])
    assert report["verdict"] == "FAIL_ODB_PAIR_NOT_FOUND"
    assert not any(case["odb_exists"] for case in report["cases"])


def test_detect_lock_file(tmp_path):
    _write_case(tmp_path, "sanity_base_power_1x", include_lck=True)
    _write_case(tmp_path, "sanity_base_power_2x")
    report = inventory_solver_outputs([tmp_path])
    base = next(case for case in report["cases"] if case["expected_role"] == "base")
    assert base["lock_exists"] is True
    assert base["warning"] == "WARNING_LOCK_FILE_PRESENT"


def _write_case(root: Path, stem: str, include_odb: bool = True, include_lck: bool = False) -> None:
    for suffix in [".inp", ".sta", ".msg", ".dat", ".log", ".com", ".prt"]:
        (root / f"{stem}{suffix}").write_text("THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n", encoding="utf-8")
    if include_odb:
        (root / f"{stem}.odb").write_bytes(b"odb-placeholder")
    if include_lck:
        (root / f"{stem}.lck").write_text("", encoding="utf-8")

