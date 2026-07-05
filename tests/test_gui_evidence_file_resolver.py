from __future__ import annotations

from pathlib import Path

from abqpilot.gui.evidence_file_resolver import common_artifact_locations, resolve_evidence_files


SMOKE_TASK = Path("D:/Projects/AbqPilot-v2/runs/tasks/stage5_0f_non_solver_revalidation_smoke")


def test_evidence_file_resolver_module_imports():
    locations = common_artifact_locations(SMOKE_TASK)
    assert "acom_result_intake" in locations


def test_evidence_resolver_finds_common_artifacts():
    resolved = resolve_evidence_files(SMOKE_TASK)
    assert resolved["acom_handoff"]["json_files"]
    assert resolved["acom_result_intake"]["json_files"]
    assert resolved["revalidation_scaffold"]["json_files"]
    assert resolved["non_solver_revalidation"]["json_files"]
    assert resolved["supervisor_review"]["json_files"]
    assert resolved["non_solver_ledger"]["json_files"]
    assert resolved["evidence_summary"]["json_files"]
    assert resolved["supervisor_ack"]["json_files"]
