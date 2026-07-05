from abqpilot.gui.beta_checklist import build_gui_beta_checklist, render_gui_beta_checklist_markdown


def test_gui_beta_checklist_imports_and_contains_all_components() -> None:
    checklist = build_gui_beta_checklist()
    text = render_gui_beta_checklist_markdown(checklist)
    assert checklist["all_passed"] is True
    assert "Stage 5.1A workflow state model" in text
    assert "Stage 5.1E next-step recommendation" in text
    assert "GUI beta readiness" in text
    assert checklist["final_evidence_approved"] is False
    assert checklist["final_verdict_frozen"] is False
