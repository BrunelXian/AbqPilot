import json

from abqpilot.gui.action_controller import GuiActionController
from abqpilot.gui.app import AbqPilotGui


def test_gui_patch_preview_imports():
    assert AbqPilotGui is not None


def test_gui_preview_guarded_patch_action(tmp_path):
    controller = GuiActionController(tmp_path)
    task = tmp_path / "task"
    task.mkdir()
    proposal_dir = task / "llm_patch_proposals"
    proposal_dir.mkdir()
    (proposal_dir / "llm_candidate_patch_proposal.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1",
                "provider": "mock",
                "model": "mock",
                "proposal_verdict": "NO_ACTION",
                "rationale": "no action",
                "candidate_patch": {
                    "patch_type": "no_action",
                    "target": "none",
                    "operation": "none",
                    "value": None,
                    "units": None,
                    "expected_effect": "none",
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
                "confidence": 0.5,
            }
        ),
        encoding="utf-8",
    )

    result = controller.preview_guarded_patch(task)

    assert result["verdict"] == "PATCH_PREVIEW_NOT_APPLICABLE"
