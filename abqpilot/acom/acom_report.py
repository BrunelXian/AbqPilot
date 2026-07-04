from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from abqpilot.acom.handoff_builder import validate_codex_handoff


def write_handoff_report(handoff_dir: str | Path) -> dict[str, Any]:
    validation = validate_codex_handoff(handoff_dir)
    root = Path(handoff_dir)
    manifest = validation.get("details") or {}
    report_path = root / "codex_handoff_report.md"
    lines = [
        "# ACOM Codex Handoff Report",
        "",
        f"- validation: `{validation['verdict']}`",
        f"- task_id: `{manifest.get('task_id')}`",
        f"- handoff_id: `{manifest.get('handoff_id')}`",
        f"- task_type: `{manifest.get('task_type')}`",
        f"- execution_mode: `{manifest.get('execution_mode')}`",
        f"- codex_auto_execution_allowed: `{manifest.get('codex_auto_execution_allowed')}`",
        f"- codex_summary_is_final_evidence: `{manifest.get('codex_summary_is_final_evidence')}`",
        f"- abqpilot_validation_required: `{manifest.get('abqpilot_validation_required')}`",
        "",
        "## Required Validators",
        "",
    ]
    for validator in manifest.get("required_abqpilot_validators", []):
        lines.append(f"- `{validator}`")
    lines.extend(["", "## Safety Flags", ""])
    for key, value in (manifest.get("safety_flags") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    if validation["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in validation["errors"])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = {
        "command": "report-codex-handoff",
        "verdict": "ACOM_HANDOFF_REPORT_READY" if validation["success"] else "ACOM_HANDOFF_REPORT_WITH_ERRORS",
        "success": validation["success"],
        "errors": validation["errors"],
        "warnings": validation["warnings"],
        "handoff_dir": str(root),
        "report_path": str(report_path),
        "details": manifest,
    }
    (root / "codex_handoff_report.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
