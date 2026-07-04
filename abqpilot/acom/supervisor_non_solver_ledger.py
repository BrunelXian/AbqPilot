from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def append_non_solver_ledger_entry(task_dir: str | Path, review: dict[str, Any]) -> dict[str, Any]:
    task = Path(task_dir)
    md_path = task / "NON_SOLVER_EVIDENCE_LEDGER.md"
    json_path = task / "NON_SOLVER_EVIDENCE_LEDGER.json"
    entry = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_id": review.get("task_id"),
        "source_revalidation_agent": review.get("reviewed_agent"),
        "source_revalidation_status": review.get("reviewed_status"),
        "supervisor_review_status": review.get("review_status"),
        "ledger_decision": review.get("gate_decision"),
        "artifacts_reviewed": review.get("artifacts_reviewed", []),
        "claim_boundary": "This ledger is non-final and non-solver only. It does not approve solver, ODB, metrics, or final evidence.",
        "limitations": review.get("warning_items", []),
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
    }
    payload = {"schema_version": "0.1", "ledger_type": "non_solver_evidence", "entries": []}
    if json_path.exists():
        existing = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(existing, dict):
            payload.update(existing)
    payload.setdefault("entries", []).append(entry)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if not md_path.exists():
        md_path.write_text(
            "# Non-Solver Evidence Ledger\n\n"
            "This ledger is non-final and non-solver only.\n"
            "It does not approve solver, ODB, metrics, or final evidence.\n",
            encoding="utf-8",
        )
    with md_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## Ledger Entry\n\n"
            f"- Task ID: `{entry['task_id']}`\n"
            f"- Source Revalidation Agent: `{entry['source_revalidation_agent']}`\n"
            f"- Source Revalidation Status: `{entry['source_revalidation_status']}`\n"
            f"- Supervisor Review Status: `{entry['supervisor_review_status']}`\n"
            f"- Ledger Decision: `{entry['ledger_decision']}`\n"
            f"- Artifacts Reviewed: `{', '.join(entry['artifacts_reviewed'])}`\n"
            f"- Claim Boundary: {entry['claim_boundary']}\n"
            f"- Limitations: `{len(entry['limitations'])}` warning item(s)\n"
            "- Final Evidence Approved: `False`\n"
            "- Final Verdict Frozen: `False`\n"
            "- Solver Approved: `False`\n"
            "- ODB Metrics Approved: `False`\n"
        )
    return {"ledger_md": str(md_path), "ledger_json": str(json_path), "entry": entry}
