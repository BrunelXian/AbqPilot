from pathlib import Path

from abqpilot.tools.odb_metrics_contract import (
    build_odb_metrics_contract,
    write_odb_extractor_preview,
    write_odb_metrics_contract,
)


CASES = [
    {"case_id": "base_power_1x", "expected_role": "base", "odb_path": "base.odb"},
    {"case_id": "power_x2", "expected_role": "power_x2", "odb_path": "x2.odb"},
]


def test_contract_includes_nt11_and_nt():
    contract = build_odb_metrics_contract(CASES)
    assert contract["temperature_field_candidates"] == ["NT11", "NT"]


def test_contract_includes_mises_metrics():
    contract = build_odb_metrics_contract(CASES)
    assert "S_Mises_max" in contract["metrics"]
    assert "S_Mises_mean_global" in contract["metrics"]


def test_contract_marks_contract_only_no_odb_read():
    contract = build_odb_metrics_contract(CASES)
    assert contract["default_behavior"] == "contract_only_no_odb_read"
    assert contract["heated_region_status"] == "TARGET_REGION_NOT_CONFIRMED"


def test_contract_is_written(tmp_path):
    path = tmp_path / "odb_metrics_extraction_contract.json"
    contract = write_odb_metrics_contract(path, CASES)
    assert path.exists()
    assert contract["comparison"]["base_case"] == "base_power_1x"


def test_preview_extractor_is_generated_but_not_executed(tmp_path):
    contract_path = tmp_path / "contract.json"
    preview_path = tmp_path / "extract_stage1_7_odb_metrics_preview.py"
    text = write_odb_extractor_preview(preview_path, contract_path)
    assert preview_path.exists()
    assert "PREVIEW_ONLY_NOT_EXECUTED" in text
    assert "odb_metrics_pair.json" in text


def test_stage1_7_default_code_has_no_process_execution():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "abqpilot" / "tools" / "solver_output_intake.py",
        root / "abqpilot" / "tools" / "solver_status_classifier.py",
        root / "abqpilot" / "tools" / "odb_metrics_contract.py",
        root / "examples" / "mvp1_am_thermal" / "run_stage1_7_manual_solver_output_intake.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = ["sub" + "process", "Po" + "pen", "os." + "system", "shell" + "=True"]
    assert not any(token in combined for token in forbidden)

