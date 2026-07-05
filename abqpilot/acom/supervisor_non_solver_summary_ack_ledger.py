from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def append_non_solver_summary_ack_ledger_entry(task_dir: str | Path, ack: dict[str, Any]) -> dict[str, Any]:
    task = Path(task_dir)
    md_path = task / "NON_SOLVER_SUMMARY_ACK_LEDGER.md"
    json_path = task / "NON_SOLVER_SUMMARY_ACK_LEDGER.json"
    entry = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_id": ack.get("task_id"),
        "evidence_summary_status": ack.get("reviewed_summary_status"),
        "supervisor_acknowledgement_status": ack.get("ack_status"),
        "gate_decision": ack.get("gate_decision"),
        "artifacts_reviewed": ack.get("artifacts_reviewed", []),
        "claim_boundary": "This acknowledgement ledger is non-final and non-solver only. It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.",
        "limitations": ack.get("warning_items", []),
        "final_evidence_approved": False,
        "final_verdict_frozen": False,
        "solver_approved": False,
        "odb_metrics_approved": False,
        "task_final_evidence_ledger_updated": False,
    }
    payload = {"schema_version": "0.1", "ledger_type": "non_solver_summary_ack", "entries": []}
    if json_path.exists():
        existing = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(existing, dict):
            payload.update(existing)
    payload.setdefault("entries", []).append(entry)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    if not md_path.exists():
        md_path.write_text(
            "# Non-Solver Summary Acknowledgement Ledger\n\n"
            "This acknowledgement ledger is non-final and non-solver only.\n"
            "It does not approve solver, ODB, metrics, model mutation, final evidence, or final verdict.\n",
            encoding="utf-8",
        )
    with md_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n## Acknowledgement Entry\n\n"
            f"- Task ID: `{entry['task_id']}`\n"
            f"- Evidence Summary Status: `{entry['evidence_summary_status']}`\n"
            f"- Supervisor Acknowledgement Status: `{entry['supervisor_acknowledgement_status']}`\n"
            f"- Gate Decision: `{entry['gate_decision']}`\n"
            f"- Artifacts Reviewed: `{', '.join(entry['artifacts_reviewed'])}`\n"
            f"- Claim Boundary: {entry['claim_boundary']}\n"
            f"- Limitations: `{len(entry['limitations'])}` warning item(s)\n"
            "- Final Evidence Approved: `False`\n"
            "- Final Verdict Frozen: `False`\n"
            "- Solver Approved: `False`\n"
            "- ODB Metrics Approved: `False`\n"
            "- Task Final Evidence Ledger Updated: `False`\n"
        )
    return {"ledger_md": str(md_path), "ledger_json": str(json_path), "entry": entry}
