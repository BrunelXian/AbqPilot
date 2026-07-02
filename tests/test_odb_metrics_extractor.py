import json
from pathlib import Path

from abqpilot.odb.odb_metrics_extractor import OdbMetricsExtractor, safe_ratio, scan_odb_script_safety


FINAL_PASS = "PASS_ABQPILOT_V2_STAGE1_8_GATED_ODB_METRICS_EXTRACTION_READY"


def test_prepare_request_fails_if_either_odb_missing(tmp_path):
    contract = _write_contract(tmp_path, make_odb=False)
    extractor = OdbMetricsExtractor(abaqus_command="disabled", allow_odb_read=True, odb_read_mode="metrics_only")

    request = extractor.prepare_request(contract, tmp_path / "out")

    assert request["verdict"] == "FAIL_ODB_PAIR_NOT_FOUND"


def test_safety_scan_rejects_unsafe_odb_script(tmp_path):
    script = tmp_path / "extract.py"
    script.write_text("from odbAccess import open" + "Odb\njob.sub" + "mit()\n", encoding="utf-8")

    scan = scan_odb_script_safety(script)

    assert scan["safe"] is False
    assert "sub" + "mit(" in scan["forbidden_hits"]


def test_mocked_subprocess_success_with_metrics_json_returns_success(monkeypatch, tmp_path):
    request, extractor = _prepared_enabled(tmp_path)

    def fake_run(command, **kwargs):
        _write_metrics_json(Path(request["metrics_json_path"]))
        fake_run.command = command
        fake_run.kwargs = kwargs
        return _Completed(0, "metrics extracted", "")

    monkeypatch.setattr("abqpilot.odb.odb_metrics_extractor.subprocess.run", fake_run)
    report = extractor.extract(request)

    assert report["verdict"] == FINAL_PASS
    assert report["executed"] is True
    assert fake_run.command == [extractor.abaqus_command, "python", request["script_path"]]
    assert fake_run.kwargs["shell"] is False


def test_mocked_subprocess_success_missing_metrics_json_returns_failure(monkeypatch, tmp_path):
    request, extractor = _prepared_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        return _Completed(0, "completed but no json", "")

    monkeypatch.setattr("abqpilot.odb.odb_metrics_extractor.subprocess.run", fake_run)
    report = extractor.extract(request)

    assert report["verdict"] == "FAIL_ODB_METRICS_JSON_MISSING"
    assert report["executed"] is True


def test_mocked_subprocess_nonzero_return_code_returns_failure(monkeypatch, tmp_path):
    request, extractor = _prepared_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        return _Completed(9, "stdout text", "stderr text")

    monkeypatch.setattr("abqpilot.odb.odb_metrics_extractor.subprocess.run", fake_run)
    report = extractor.extract(request)

    assert report["verdict"] == "FAIL_ODB_EXTRACT_COMMAND_FAILED"
    assert report["return_code"] == 9


def test_report_includes_execution_details(monkeypatch, tmp_path):
    request, extractor = _prepared_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        _write_metrics_json(Path(request["metrics_json_path"]))
        return _Completed(0, "stdout tail", "stderr tail")

    monkeypatch.setattr("abqpilot.odb.odb_metrics_extractor.subprocess.run", fake_run)
    report = extractor.extract(request)

    saved = json.loads(Path(request["output_dir"], "odb_metrics_extraction_report.json").read_text(encoding="utf-8"))
    for payload in (report, saved):
        assert payload["executed"] is True
        assert payload["return_code"] == 0
        assert payload["stdout_tail"] == "stdout tail"
        assert payload["stderr_tail"] == "stderr tail"
        assert payload["metrics_json_path"] == request["metrics_json_path"]


def test_contract_supports_nt11_and_nt(tmp_path):
    contract_path = _write_contract(tmp_path, make_odb=True)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract["temperature_field_candidates"] == ["NT11", "NT"]


def test_comparison_ratios_handle_divide_by_zero_safely():
    assert safe_ratio(0, 10) is None
    assert safe_ratio(None, 10) is None
    assert safe_ratio(5, None) is None
    assert safe_ratio(5, 10) == 2


def test_extract_remains_disabled_when_gate_false(tmp_path):
    request, _extractor = _prepared_enabled(tmp_path)
    disabled = OdbMetricsExtractor(
        abaqus_command=request["abaqus_command"],
        allow_odb_read=False,
        odb_read_mode="metrics_only",
        allow_solver_submit=False,
        allow_abqjobpilot=False,
        allow_llm=False,
    )
    report = disabled.extract(request)
    assert report["verdict"] == "ODB_READ_DISABLED"
    assert report["executed"] is False


def _prepared_enabled(tmp_path) -> tuple[dict, OdbMetricsExtractor]:
    command = tmp_path / "abq2024.bat"
    command.write_text("@echo off\n", encoding="utf-8")
    contract = _write_contract(tmp_path, make_odb=True)
    extractor = OdbMetricsExtractor(
        abaqus_command=str(command),
        allow_odb_read=True,
        odb_read_mode="metrics_only",
        allow_solver_submit=False,
        allow_abqjobpilot=False,
        allow_llm=False,
        timeout_s=10,
    )
    request = extractor.prepare_request(contract, tmp_path / "out")
    assert request["verdict"] == "ODB_METRICS_REQUEST_PREPARED"
    return request, extractor


def _write_contract(tmp_path, make_odb: bool) -> Path:
    base_odb = tmp_path / "base.odb"
    x2_odb = tmp_path / "x2.odb"
    if make_odb:
        base_odb.write_bytes(b"placeholder")
        x2_odb.write_bytes(b"placeholder")
    contract = {
        "cases": [
            {"case_id": "base_power_1x", "role": "base", "odb_path": str(base_odb)},
            {"case_id": "power_x2", "role": "power_x2", "odb_path": str(x2_odb)},
        ],
        "temperature_field_candidates": ["NT11", "NT"],
        "stress_field": "S",
        "frame_selection": {"preferred": "last_frame", "cooling_time_s": 100.0},
    }
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return path


def _write_metrics_json(path: Path) -> None:
    payload = {
        "cases": [
            {
                "case_id": "base_power_1x",
                "role": "base",
                "status": "METRICS_EXTRACTED",
                "metrics": {"NT_max": 1.0, "S_Mises_max": 2.0},
                "missing_fields": [],
            },
            {
                "case_id": "power_x2",
                "role": "power_x2",
                "status": "METRICS_EXTRACTED",
                "metrics": {"NT_max": 2.0, "S_Mises_max": 4.0},
                "missing_fields": [],
            },
        ],
        "comparison": {
            "power_x2_minus_base": {"NT_max_delta": 1.0},
            "power_x2_over_base": {"NT_max_ratio": 2.0},
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class _Completed:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
