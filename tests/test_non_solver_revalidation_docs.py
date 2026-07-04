from __future__ import annotations

from pathlib import Path


def test_non_solver_revalidation_docs_define_scope():
    text = Path("docs/ACOM_NON_SOLVER_REVALIDATION.md").read_text(encoding="utf-8")
    assert "DocsStatusAgent" in text
    assert "SoftwareQAAgent" in text
    assert "GuardAgent" in text
    assert "blocked" in text.lower()
    assert "not final evidence accepted" in text


def test_agents_md_mentions_stage5_0f_boundaries():
    text = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "Non-solver revalidation" in text
    assert "High-risk model/solver/ODB agents must be blocked" in text
    assert "does not approve final evidence" in text
