from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acom_result_revalidation_doc_states_pending_not_evidence() -> None:
    text = (ROOT / "docs" / "ACOM_RESULT_PIPELINE_REVALIDATION.md").read_text(encoding="utf-8")
    assert "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION" in text
    assert "not accepted as final evidence" in text
    assert "PENDING_REVALIDATION" in text
    assert "Unsafe safety flags" in text or "Safety Rejection" in text


def test_agents_policy_blocks_direct_evidence_approval() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "ACOM result intake must never directly approve evidence" in text
    assert "Codex summaries are not evidence" in text
    assert "Unsafe safety flags must block result intake" in text or "reject unsafe safety flags" in text


def test_cli_and_gui_docs_include_acom_result_intake_actions() -> None:
    cli_text = (ROOT / "docs" / "CLI_USAGE.md").read_text(encoding="utf-8")
    gui_text = (ROOT / "docs" / "GUI_BETA.md").read_text(encoding="utf-8")
    assert "report-acom-result-intake" in cli_text
    assert "Intake ACOM Result" in gui_text
    assert "Report ACOM Result Intake" in gui_text
