from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.gui.high_risk_gate_catalog import get_high_risk_gate_catalog
from abqpilot.gui.high_risk_gate_ux import build_high_risk_gate_ux


STAGE5_2A_VERDICT = "PASS_ABQPILOT_V2_STAGE5_2A_GUI_HIGH_RISK_GATE_UX_SPEC_READY"


def build_high_risk_gate_ux_spec(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    catalog = get_high_risk_gate_catalog()
    previews = [build_high_risk_gate_ux(str(action["action_id"])) for action in catalog]
    return {
        "schema_version": "0.1",
        "stage": "Stage 5.2A",
        "stage_id": "STAGE5_2A",
        "verdict": STAGE5_2A_VERDICT,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "preview_only": True,
        "specification_only": True,
        "not_approved": True,
        "not_executable": True,
        "high_risk_actions": catalog,
        "gate_previews": previews,
        "action_count": len(catalog),
        "all_actions_disabled": all(action["default_allowed"] is False for action in catalog),
        "all_actions_preview_only": all(action["preview_only"] is True for action in catalog),
        "all_actions_require_human_gate": all(action["requires_human_gate"] is True for action in catalog),
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "queue_runner_launched": False,
        "codex_cli_called": False,
        "auto_execute_allowed": False,
        "real_gate_created": False,
        "task_final_evidence_ledger_updated": False,
        "safety_boundary": (
            "No solver, ODB, queue, Codex, scheduling, final evidence approval, final verdict freeze, "
            "real gate creation, or TASK_FINAL_EVIDENCE_LEDGER.md mutation is enabled in Stage 5.2A."
        ),
        "known_limitations": [
            "This is a GUI UX specification only.",
            "Prerequisites are advisory until a future explicit gate implementation.",
            "No task gates/ records are created as approvals.",
        ],
    }


def write_high_risk_gate_ux_spec(project_root: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root)
    out = Path(output_dir) if output_dir else root / "gui_high_risk_gate_ux"
    out.mkdir(parents=True, exist_ok=True)

    from abqpilot.gui.high_risk_gate_report import (
        render_high_risk_action_catalog_markdown,
        render_high_risk_gate_checklists_markdown,
        render_high_risk_gate_ux_report,
    )

    spec = build_high_risk_gate_ux_spec(root)
    spec_path = out / "HIGH_RISK_GATE_UX_SPEC.json"
    report_path = out / "HIGH_RISK_GATE_UX_SPEC_REPORT.md"
    catalog_path = out / "HIGH_RISK_ACTION_CATALOG.md"
    checklists_path = out / "HIGH_RISK_GATE_CHECKLISTS.md"

    import json

    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_high_risk_gate_ux_report(spec), encoding="utf-8")
    catalog_path.write_text(render_high_risk_action_catalog_markdown(spec["high_risk_actions"]), encoding="utf-8")
    checklists_path.write_text(render_high_risk_gate_checklists_markdown(spec["gate_previews"]), encoding="utf-8")
    return {
        "command": "report-gui-high-risk-gates",
        "verdict": "GUI_HIGH_RISK_GATE_UX_SPEC_REPORT_READY",
        "success": True,
        "output_paths": {
            "spec_json": str(spec_path),
            "spec_report": str(report_path),
            "action_catalog": str(catalog_path),
            "gate_checklists": str(checklists_path),
        },
        "details": spec,
        "warnings": [],
        "errors": [],
    }
