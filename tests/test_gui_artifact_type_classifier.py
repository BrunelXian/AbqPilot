from pathlib import Path

from abqpilot.gui.artifact_type_classifier import classify_artifact


def test_artifact_classifier_identifies_frontmatter_types(tmp_path: Path) -> None:
    assert classify_artifact(tmp_path / "RUN_001.md", frontmatter={"doc_type": "run_report"}) == "RUN_REPORT"
    assert classify_artifact(tmp_path / "HANDOFF_001.md", frontmatter={"doc_type": "handoff"}) == "HANDOFF"
    assert classify_artifact(tmp_path / "GATE_001.md", frontmatter={"doc_type": "gate_decision"}) == "GATE_DECISION"


def test_artifact_classifier_identifies_known_artifact_names(tmp_path: Path) -> None:
    assert classify_artifact(tmp_path / "NON_SOLVER_EVIDENCE_LEDGER.json") == "NON_SOLVER_EVIDENCE_LEDGER"
    assert classify_artifact(tmp_path / "NON_SOLVER_EVIDENCE_SUMMARY_RESULT.json") == "NON_SOLVER_EVIDENCE_SUMMARY"
    assert classify_artifact(tmp_path / "SUPERVISOR_NON_SOLVER_SUMMARY_ACK_RESULT.json") == "SUPERVISOR_SUMMARY_ACK"
