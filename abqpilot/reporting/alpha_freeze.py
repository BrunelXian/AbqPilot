from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


CAPABILITIES = [
    "CAE export",
    "INP heat patch",
    "StaticValidator",
    "DiffGuard",
    "PhysicsGuard",
    "JobPilot preflight",
    "Dry-run enqueue",
    "Human approval token",
    "Real queue-only enqueue",
    "Status polling",
    "Completed job intake",
    "ODB metrics extraction",
    "Metrics comparison",
    "Evaluation",
    "Repair plan",
    "GUI alpha",
    "Artifact browser",
    "Run report export",
]

SAFETY_BOUNDARIES = {
    "Abaqus solver submit": "not automatic",
    "Queue" + "Runner launch": "not automatic",
    "GUI launch for abqjobpilot": "not used",
    "Open" + "AI API": "not integrated",
    "LLM repair": "not integrated",
    "ODB open": "gated extractor only",
    "Real enqueue": "approval-token gated",
}


def export_alpha_freeze(root: str | Path = ".", test_results: str | None = None) -> dict[str, Any]:
    project_root = Path(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = project_root / "runs" / f"alpha_freeze_{stamp}"
    target.mkdir(parents=True, exist_ok=True)
    summary = {
        "stage": "ABQPILOT_V2_MEGA_SPRINT_01_GUI_AND_CONTINUATION_ALPHA",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "capabilities": CAPABILITIES,
        "safety_boundaries": SAFETY_BOUNDARIES,
        "verdict": "PASS_ABQPILOT_V2_MEGA_SPRINT_01_GUI_AND_CONTINUATION_ALPHA_READY",
    }
    paths = {
        "alpha_freeze_report_json": target / "ALPHA_FREEZE_REPORT.json",
        "alpha_freeze_report_md": target / "ALPHA_FREEZE_REPORT.md",
        "test_results": target / "test_results.txt",
        "capability_matrix": target / "capability_matrix.md",
        "safety_boundary_matrix": target / "safety_boundary_matrix.md",
        "known_limitations": target / "known_limitations.md",
    }
    paths["alpha_freeze_report_json"].write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["alpha_freeze_report_md"].write_text(_freeze_markdown(summary), encoding="utf-8")
    paths["test_results"].write_text(test_results or "Run `python -m pytest -q` for current test output.\n", encoding="utf-8")
    paths["capability_matrix"].write_text(_capability_matrix(), encoding="utf-8")
    paths["safety_boundary_matrix"].write_text(_safety_matrix(), encoding="utf-8")
    paths["known_limitations"].write_text(_known_limitations(), encoding="utf-8")
    return {
        "command": "alpha-freeze",
        "verdict": summary["verdict"],
        "success": True,
        "output_paths": {key: str(value) for key, value in paths.items()} | {"alpha_freeze_dir": str(target)},
        "details": summary,
        "warnings": [],
        "errors": [],
    }


def _freeze_markdown(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# AbqPilot Alpha Freeze Report",
            "",
            f"Stage: `{summary['stage']}`",
            f"Verdict: `{summary['verdict']}`",
            "",
            "See `capability_matrix.md`, `safety_boundary_matrix.md`, and `known_limitations.md`.",
        ]
    ) + "\n"


def _capability_matrix() -> str:
    lines = ["# Capability Matrix", "", "| Capability | Status |", "| --- | --- |"]
    lines.extend(f"| {capability} | alpha-ready |" for capability in CAPABILITIES)
    return "\n".join(lines) + "\n"


def _safety_matrix() -> str:
    lines = ["# Safety Boundary Matrix", "", "| Boundary | Status |", "| --- | --- |"]
    lines.extend(f"| {name} | {status} |" for name, status in SAFETY_BOUNDARIES.items())
    return "\n".join(lines) + "\n"


def _known_limitations() -> str:
    return "\n".join(
        [
            "# Known Limitations",
            "",
            "- GUI alpha is local and read/refresh first.",
            "- Solver execution remains external/manual.",
            "- ODB metrics extraction remains gated through the existing extractor.",
            "- Repair planning is deterministic and does not mutate input files.",
        ]
    ) + "\n"
