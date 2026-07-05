from pathlib import Path

from abqpilot.gui.controlled_solver_readiness import build_solver_readiness_checklist


def _task(tmp_path: Path) -> Path:
    task = tmp_path / "task"
    (task / "trace").mkdir(parents=True)
    (task / "candidate").mkdir()
    (task / "candidate" / "candidate.inp").write_text("*Heading\n", encoding="utf-8")
    (task / "validators.md").write_text(
        "StaticValidator PASS\nDiffGuard PASS\nPhysicsGuard PASS\nMCPGuard PASS\ntarget modification\nforbidden\n",
        encoding="utf-8",
    )
    (task / "patch_preview.md").write_text("preview", encoding="utf-8")
    return task


def test_readiness_checklist_contains_required_validator_items(tmp_path: Path) -> None:
    result = build_solver_readiness_checklist(_task(tmp_path))
    ids = {item["item_id"] for item in result["checklist"]}
    assert {"static_validator_pass", "diff_guard_pass", "physics_guard_pass", "mcpguard_pass_or_not_applicable"} <= ids


def test_readiness_blocks_source_sanity_base_inp(tmp_path: Path) -> None:
    source = tmp_path / "source_sanity_base_export.inp"
    source.write_text("*Heading\n", encoding="utf-8")
    result = build_solver_readiness_checklist(_task(tmp_path), candidate_inp=source)
    assert result["readiness_status"] == "SOLVER_GATE_PREVIEW_BLOCKED_SOURCE_MUTATION_RISK"


def test_readiness_blocks_execution_request_present(tmp_path: Path) -> None:
    task = _task(tmp_path)
    (task / "solver_request.json").write_text("{}", encoding="utf-8")
    result = build_solver_readiness_checklist(task)
    assert result["readiness_status"] == "SOLVER_GATE_PREVIEW_BLOCKED_EXECUTION_REQUEST_PRESENT"


def test_readiness_blocks_final_evidence_request_present(tmp_path: Path) -> None:
    task = _task(tmp_path)
    (task / "unsafe.json").write_text('{"final_evidence_approved": true}', encoding="utf-8")
    result = build_solver_readiness_checklist(task)
    assert "no_final_evidence_update_requested" in result["missing_prerequisites"]
