from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.artifact_preview import build_artifact_preview
from abqpilot.gui.read_only_document_view import build_read_only_document_view
from abqpilot.gui.report_viewer import build_report_viewer_card, render_report_viewer_text
from abqpilot.gui.timeline_interaction import select_timeline_step


def build_trace_detail_card(task_dir: str | Path | None, step_id: str) -> dict[str, Any]:
    selection = select_timeline_step(task_dir, step_id)
    step = selection["selected_step"]
    preview_paths = (
        step.get("related_run_files", [])
        + step.get("related_gate_files", [])
        + step.get("related_handoff_files", [])
        + step.get("related_json_files", [])
        + step.get("related_markdown_reports", [])
    )
    unique_paths = _unique(preview_paths[:6])
    previews = [build_read_only_document_view(path, max_lines=12) for path in unique_paths]
    artifact_previews = [build_artifact_preview(path) for path in unique_paths]
    report_cards = [build_report_viewer_card(path) for path in unique_paths]
    return {
        "title": step.get("display_name"),
        "current_status": step.get("status"),
        "related_files": {
            "RUN": step.get("related_run_files", []),
            "HANDOFF": step.get("related_handoff_files", []),
            "GATE": step.get("related_gate_files", []),
            "JSON": step.get("related_json_files", []),
            "MARKDOWN": step.get("related_markdown_reports", []),
        },
        "latest_run_verdict": step.get("latest_verdict"),
        "latest_gate_decision": step.get("latest_decision"),
        "latest_handoff_target": step.get("latest_handoff_target"),
        "claim_boundary": step.get("claim_boundary"),
        "safety_boundary": step.get("safety_boundary"),
        "missing_files": step.get("missing_expected_files", []),
        "next_safe_action": "Inspect related records only.",
        "document_previews": previews,
        "artifact_previews": artifact_previews,
        "report_viewer_cards": report_cards,
        "read_only": True,
        "action_allowed": False,
    }


def render_trace_detail_text(card: dict[str, Any]) -> str:
    lines = [
        "Read-only trace viewer",
        str(card.get("title")),
        "",
        "Current Status",
        str(card.get("current_status")),
        "",
        "Latest RUN Verdict",
        str(card.get("latest_run_verdict")),
        "",
        "Latest GATE Decision",
        str(card.get("latest_gate_decision")),
        "",
        "Latest HANDOFF Target",
        str(card.get("latest_handoff_target")),
        "",
        "Claim Boundary",
        str(card.get("claim_boundary")),
        "",
        "Safety Boundary",
        str(card.get("safety_boundary")),
        "Final evidence remains locked",
        "Solver / ODB / metrics are disabled",
        "Codex output is displayed as structured input, not final evidence",
        "Non-solver summary acknowledgement is non-final",
        "",
        "Related Files",
    ]
    files = card.get("related_files", {})
    for group_name, paths in files.items():
        lines.append(f"{group_name}: {len(paths)}")
        lines.extend(f"- {path}" for path in paths[:8])
    missing = card.get("missing_files", [])
    if missing:
        lines.extend(["", "Missing Expected Files"])
        lines.extend(f"- {item}" for item in missing)
    cards = card.get("report_viewer_cards", [])
    if cards:
        lines.extend(["", "Artifact Previews"])
        for item in cards[:3]:
            lines.append("")
            lines.append(render_report_viewer_text(item))
    return "\n".join(lines)


def _unique(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            result.append(path)
    return result
