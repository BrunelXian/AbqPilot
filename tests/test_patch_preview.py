import json
from pathlib import Path

from abqpilot.patching.patch_preview import preview_patch


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "mvp1_am_thermal" / "base_heatflux_marker.inp"


def test_missing_proposal_blocks(tmp_path):
    task = _task(tmp_path)

    result = preview_patch(task)

    assert result["verdict"] == "PATCH_PREVIEW_BLOCKED_NO_VALID_PROPOSAL"


def test_no_action_proposal_is_not_applicable(tmp_path):
    task = _task(tmp_path)
    _write_proposal(task, "NO_ACTION", "no_action")

    result = preview_patch(task)

    assert result["verdict"] == "PATCH_PREVIEW_NOT_APPLICABLE"
    assert result["details"]["candidate_inp_path"] is None


def test_heat_flux_preview_creates_candidate_and_preserves_source(tmp_path):
    task = _task(tmp_path)
    source = tmp_path / "source.inp"
    source.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
    original = source.read_text(encoding="utf-8")
    proposal = _write_proposal(task, "PATCH_PROPOSED", "heat_flux_magnitude_adjustment", value=1.25)

    result = preview_patch(task, proposal_path=proposal, source_inp=source)

    assert result["verdict"] == "PATCH_PREVIEW_READY"
    assert source.read_text(encoding="utf-8") == original
    candidate = Path(result["details"]["candidate_inp_path"])
    assert candidate.exists()
    assert result["details"]["changed_lines_count"] == 1
    assert result["details"]["static_validator_status"] == "PASS"
    assert result["details"]["diff_guard_status"] == "PASS"
    assert result["details"]["physics_guard_status"] == "PASS"
    assert result["details"]["unrelated_changes_count"] == 0


def test_failed_static_validator_blocks_preview(tmp_path):
    task = _task(tmp_path)
    source = tmp_path / "source_missing_nt.inp"
    source.write_text(BASE.read_text(encoding="utf-8").replace("NT11", ""), encoding="utf-8")
    proposal = _write_proposal(task, "PATCH_PROPOSED", "heat_flux_magnitude_adjustment", value=1.1)

    result = preview_patch(task, proposal_path=proposal, source_inp=source)

    assert result["verdict"] == "PATCH_PREVIEW_FAILED_VALIDATION"
    assert result["details"]["static_validator_status"] == "FAIL"


def _task(tmp_path):
    task = tmp_path / "task"
    task.mkdir()
    return task


def _write_proposal(task, verdict, patch_type, value=None):
    proposal_dir = task / "llm_patch_proposals"
    proposal_dir.mkdir(exist_ok=True)
    proposal = {
        "schema_version": "0.1",
        "provider": "mock",
        "model": "mock",
        "proposal_verdict": verdict,
        "rationale": "test proposal",
        "candidate_patch": {
            "patch_type": patch_type,
            "target": "heat_flux_magnitude" if patch_type == "heat_flux_magnitude_adjustment" else "none",
            "operation": "scale" if patch_type == "heat_flux_magnitude_adjustment" else "none",
            "value": value,
            "units": None,
            "expected_effect": "test",
            "requires_human_review": True,
        },
        "guard_requirements": {
            "requires_static_validator": True,
            "requires_diff_guard": True,
            "requires_physics_guard": True,
            "requires_human_approval": True,
        },
        "blocked_actions": ["solver_submit"],
        "risk_flags": [],
        "confidence": 0.8,
    }
    path = proposal_dir / "llm_candidate_patch_proposal.json"
    path.write_text(json.dumps(proposal), encoding="utf-8")
    return path
