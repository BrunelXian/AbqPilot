from abqpilot.gui.section_extractor import extract_headings, extract_key_sections


def test_section_extractor_extracts_headings_and_key_sections() -> None:
    body = """# Report

## Purpose
Explain the task.

## Claim Boundary
Non-final only.

## Safety Boundary
No solver.
"""
    headings = extract_headings(body)
    sections = extract_key_sections(body)
    assert [item["title"] for item in headings] == ["Report", "Purpose", "Claim Boundary", "Safety Boundary"]
    assert "Non-final only." in sections["Claim Boundary"]
    assert "No solver." in sections["Safety Boundary"]
