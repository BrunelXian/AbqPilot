from pathlib import Path


def test_agents_md_contains_sanity_base_hard_rule():
    root = Path(__file__).resolve().parents[1]
    text = (root / "AGENTS.md").read_text(encoding="utf-8")

    assert "## Hard Rule: SanityBase-Derived Simulation Candidates Only" in text
    assert "sanity_base_v01.cae" in text
    assert "WARNING_ABQPILOT_SIMULATION_SOURCE_NOT_SANITY_BASE_DERIVED" in text
    assert "tiny fixture files such as 1 KB INP snippets" in text
