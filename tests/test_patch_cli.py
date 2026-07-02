import json
from pathlib import Path

from abqpilot import cli


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "mvp1_am_thermal" / "base_heatflux_marker.inp"


def test_cli_preview_patch_no_action(tmp_path):
    task = _task(tmp_path)
    _write_proposal(task, "NO_ACTION", "no_action")

    result = cli.command_preview_patch(task_dir=task)

    assert result["verdict"] == "PATCH_PREVIEW_NOT_APPLICABLE"


def test_cli_preview_patch_safe_heat_flux_fixture(tmp_path):
    task = _task(tmp_path)
    source = tmp_path / "source.inp"
    source.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
    proposal = _write_proposal(task, "PATCH_PROPOSED", "heat_flux_magnitude_adjustment", value=1.2)

    result = cli.command_preview_patch(task_dir=task, proposal_path=proposal, source_inp=source)

    assert result["verdict"] == "PATCH_PREVIEW_READY"
    assert result["details"]["static_validator_status"] == "PASS"
    assert result["details"]["diff_guard_status"] == "PASS"
    assert result["details"]["physics_guard_status"] == "PASS"
    assert result["details"]["job_enqueued"] is False
    assert result["details"]["solver_submitted"] is False


def test_parser_accepts_preview_patch():
    args = cli.build_parser().parse_args(["preview-patch", "--task-dir", "task", "--provider-source", "llm"])

    assert args.command == "preview-patch"


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
            "target": "heat_flux_magnitude",
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
        "blocked_actions": [],
        "risk_flags": [],
        "confidence": 0.7,
    }
    path = proposal_dir / "llm_candidate_patch_proposal.json"
    path.write_text(json.dumps(proposal), encoding="utf-8")
    return path
