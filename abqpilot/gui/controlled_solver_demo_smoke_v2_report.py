from __future__ import annotations

from typing import Any


def render_demo_smoke_v2_report(result: dict[str, Any]) -> str:
    status = result.get("status", result)
    return "\n".join([
        "# Controlled Solver Demo Smoke Run v2", "", f"Verdict: `{result.get('verdict', status.get('solver_status'))}`", "",
        "Stage 5.3A-v2 is the first controlled Abaqus demo invocation retry after workspace remediation.",
        "It is limited to the dedicated Stage 5.3A-v2 smoke task.",
        "No ODB is opened. Metrics are not extracted. Final evidence remains locked.", "", "## Input",
        f"- Source INP: `{result.get('source_inp_path')}`", f"- Source SHA256: `{result.get('source_inp_sha256')}`",
        f"- Copied INP: `{result.get('copied_inp_path')}`", f"- Copied SHA256: `{result.get('copied_inp_sha256')}`", "", "## Solver Status",
        f"- Solver invoked: `{status.get('solver_invoked')}`", f"- Solver status: `{status.get('solver_status')}`", f"- Return code: `{status.get('solver_return_code')}`",
        f"- ODB produced: `{status.get('odb_produced')}`", f"- ODB opened: `{status.get('odb_opened')}`", f"- Metrics extracted: `{status.get('metrics_extracted')}`", f"- Final evidence approved: `{status.get('final_evidence_approved')}`",
    ])


def render_demo_smoke_v2_audit(audit: dict[str, Any]) -> str:
    lines = ["# Controlled Solver Demo Smoke v2 Safety Audit", "", f"Audit status: `{audit.get('audit_status')}`", ""]
    for key, value in sorted(audit.get("checks", {}).items()):
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines)
