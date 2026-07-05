from pathlib import Path

from abqpilot.gui.json_preview import build_json_preview


def test_json_preview_parses_keys_status_decision_and_pretty_json(tmp_path: Path) -> None:
    path = tmp_path / "NON_SOLVER_EVIDENCE_LEDGER.json"
    path.write_text(
        '{"status":"READY","decision":"ACK","final_evidence_approved":false,"safety_flags":{"solver_run":false}}',
        encoding="utf-8",
    )
    preview = build_json_preview(path)
    assert preview["parse_status"] == "ARTIFACT_PREVIEW_READY"
    assert preview["artifact_type"] == "NON_SOLVER_EVIDENCE_LEDGER"
    assert "status" in preview["top_level_keys"]
    assert preview["status_fields"]["status"] == "READY"
    assert preview["decision_fields"]["decision"] == "ACK"
    assert '"status": "READY"' in preview["pretty_json"]


def test_json_preview_reports_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    preview = build_json_preview(path)
    assert preview["parse_status"] == "ARTIFACT_PREVIEW_PARSE_ERROR"


def test_json_preview_flags_nested_unsafe_claim(tmp_path: Path) -> None:
    path = tmp_path / "unsafe.json"
    path.write_text('{"safety_flags":{"odb_opened":true}}', encoding="utf-8")
    preview = build_json_preview(path)
    assert preview["parse_status"] == "ARTIFACT_PREVIEW_BLOCKED_UNSAFE_FINAL_APPROVAL_CLAIM"
    assert preview["unsafe_claims"][0]["key"] == "safety_flags.odb_opened"
