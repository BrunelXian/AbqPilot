from pathlib import Path

from abqpilot.gui.high_risk_gate_preview import build_high_risk_gate_ux_spec, write_high_risk_gate_ux_spec


def test_high_risk_gate_spec_flags_are_non_final(tmp_path: Path) -> None:
    spec = build_high_risk_gate_ux_spec(tmp_path)
    assert spec["preview_only"] is True
    assert spec["specification_only"] is True
    assert spec["final_evidence_approved"] is False
    assert spec["final_verdict_frozen"] is False
    assert spec["solver_approved"] is False
    assert spec["odb_metrics_approved"] is False
    assert spec["codex_cli_called"] is False
    assert spec["queue_runner_launched"] is False
    assert spec["auto_execute_allowed"] is False
    assert spec["real_gate_created"] is False
    assert spec["task_final_evidence_ledger_updated"] is False


def test_write_high_risk_gate_spec_outputs(tmp_path: Path) -> None:
    result = write_high_risk_gate_ux_spec(tmp_path)
    assert result["verdict"] == "GUI_HIGH_RISK_GATE_UX_SPEC_REPORT_READY"
    paths = result["output_paths"]
    for path in paths.values():
        assert Path(path).exists()
    report = Path(paths["spec_report"]).read_text(encoding="utf-8")
    assert "Preview only; not an approval" in report
    assert "No real gate is created in Stage 5.2A" in report
