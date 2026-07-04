from __future__ import annotations

import json
from pathlib import Path

from abqpilot.acom.handoff_builder import validate_codex_handoff
from abqpilot.acom.template_renderer import render_pipeline_acom_handoff
from abqpilot.pipeline_protocol.frontmatter import load_frontmatter
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


def test_renderer_creates_pipeline_records_and_codex_package(tmp_path) -> None:
    result = render_pipeline_acom_handoff(
        task_id="render_smoke",
        template_id="mcpguard_review",
        project_root=tmp_path,
        title="MCPGuard smoke",
        objective="Review MCPGuard artifacts.",
    )
    assert result["verdict"] == "ACOM_PIPELINE_HANDOFF_GENERATED"
    run_path = Path(result["run_record_path"])
    handoff_path = Path(result["pipeline_handoff_path"])
    handoff_dir = Path(result["handoff_dir"])
    assert run_path.exists()
    assert handoff_path.exists()
    assert handoff_dir.exists()
    assert load_frontmatter(run_path)["doc_type"] == "run_report"
    assert load_frontmatter(handoff_path)["doc_type"] == "handoff"
    assert validate_codex_handoff(handoff_dir)["verdict"] == "ACOM_HANDOFF_VALID"
    assert validate_task_protocol(result["task_dir"])["verdict"] == "PIPELINE_PROTOCOL_VALID"


def test_renderer_evidence_contract_marks_summary_not_final_and_requires_mcpguard(tmp_path) -> None:
    result = render_pipeline_acom_handoff(task_id="evidence", template_id="guarded_candidate_preview", project_root=tmp_path)
    evidence = json.loads((Path(result["handoff_dir"]) / "evidence_contract.json").read_text(encoding="utf-8"))
    assert evidence["requires_structured_result_json"] is True
    assert evidence["codex_summary_is_final_evidence"] is False
    assert evidence["requires_mcpguard_result_for_model_mutation_or_inp_patch"] is True
    assert evidence["requires_original_condition_preservation_check"] is True
