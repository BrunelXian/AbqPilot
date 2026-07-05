from __future__ import annotations

import re
from typing import Any


KEY_SECTION_NAMES = (
    "Purpose",
    "Inputs",
    "Outputs",
    "Validation",
    "Verdict",
    "Claim Boundary",
    "Safety Boundary",
    "Guardrails",
    "Forbidden Actions Confirmation",
    "Next Recommended Step",
    "Known Limitations",
    "Ledger Decision",
    "Acknowledgement Decision",
    "Summary Scope",
    "Non-Solver Ledger Summary",
    "Supervisor Checks",
    "Pass / Warning / Fail Items",
)


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def extract_headings(markdown_body: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for line_number, line in enumerate(markdown_body.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append(
                {
                    "level": len(match.group(1)),
                    "title": match.group(2).strip(),
                    "line": line_number,
                }
            )
    return headings


def extract_key_sections(markdown_body: str) -> dict[str, str]:
    sections = _split_sections(markdown_body)
    selected: dict[str, str] = {}
    for key in KEY_SECTION_NAMES:
        match_title = _find_matching_title(key, sections)
        if match_title:
            selected[key] = sections[match_title].strip()
    return selected


def _split_sections(markdown_body: str) -> dict[str, str]:
    lines = markdown_body.splitlines()
    headings = extract_headings(markdown_body)
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        start = int(heading["line"])
        end = int(headings[index + 1]["line"]) - 1 if index + 1 < len(headings) else len(lines)
        title = str(heading["title"])
        sections[title] = "\n".join(lines[start:end])
    return sections


def _find_matching_title(target: str, sections: dict[str, str]) -> str | None:
    normalized_target = _normalize(target)
    for title in sections:
        normalized_title = _normalize(title)
        if normalized_target == normalized_title or normalized_target in normalized_title:
            return title
    return None


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
