from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from abqpilot.acom.revalidation_profiles import agent_for_template, profile_for_agent
from abqpilot.acom.revalidation_report import (
    render_expected_outputs,
    render_gate_record,
    render_handoff_record,
    render_revalidation_checklist,
    render_revalidation_inputs,
    render_revalidation_plan,
    render_run_record,
    render_scaffold_report,
)
from abqpilot.acom.revalidation_schema import SCHEMA_VERSION, STAGE, validate_revalidation_scaffold
from abqpilot.pipeline_protocol.protocol_report import generate_protocol_report
from abqpilot.pipeline_protocol.protocol_validator import validate_task_protocol


ACCEPTED_STATUS = "ACOM_RESULT_ACCEPTED_PENDING_REVALIDATION"


def scaffold_acom_revalidation(
    task_dir: str | Path,
    downstream_agent: str | None = None,
    revalidation_id: str | None = None,
) -> dict[str, Any]:
    task = Path(task_dir)
    intake_path = task / "codex_result" / "acom_result_intake.json"
    if not intake_path.exists():
        return _blocked(task, "REVALIDATION_SCAFFOLD_BLOCKED_MISSING_ACOM_INTAKE", [f"missing ACOM intake: {intake_path}"])
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    if intake.get("result_status") != ACCEPTED_STATUS:
        return _blocked(
            task,
            "REVALIDATION_SCAFFOLD_BLOCKED_ACOM_RESULT_NOT_ACCEPTED",
            [f"ACOM result status is {intake.get('result_status')}"],
            intake,
        )
    selected_agent = downstream_agent or agent_for_template(intake.get("template_id"), intake.get("downstream_agent"))
    if not selected_agent:
        return _blocked(task, "REVALIDATION_SCAFFOLD_BLOCKED_UNKNOWN_DOWNSTREAM_AGENT", ["missing downstream agent"], intake)
    profile = profile_for_agent(selected_agent)
    if profile is None:
        return _blocked(task, "REVALIDATION_SCAFFOLD_BLOCKED_UNKNOWN_DOWNSTREAM_AGENT", [f"unknown downstream agent: {selected_agent}"], intake)
    source_handoff = Path(intake.get("downstream_handoff_path", ""))
    if not source_handoff.exists():
        return _blocked(task, "REVALIDATION_SCAFFOLD_BLOCKED_MISSING_HANDOFF", [f"missing downstream handoff: {source_handoff}"], intake)

    task_id = intake.get("task_id") or task.name
    reval_id = revalidation_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    package_dir = task / "revalidation" / f"{selected_agent}_{reval_id}"
    package_dir.mkdir(parents=True, exist_ok=True)
    for child in ("trace", "handoffs", "gates"):
        (task / child).mkdir(parents=True, exist_ok=True)
    run_id = _next_available_id(task / "trace", "RUN", 13)
    gate_id = _next_available_id(task / "gates", "GATE", 9)
    handoff_id = _next_available_id(task / "handoffs", "HANDOFF", 12)
    run_path = task / "trace" / f"{run_id}_{_agent_token(selected_agent)}_REVALIDATION.md"
    gate_path = task / "gates" / f"{gate_id}_{_agent_token(selected_agent)}_REVALIDATION.md"
    handoff_path = task / "handoffs" / f"{handoff_id}_{_agent_token(selected_agent)}_REVALIDATION_TO_{_agent_token(profile.next_agent)}.md"

    scaffold = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "task_id": task_id,
        "task_dir": str(task),
        "status": "REVALIDATION_SCAFFOLD_READY",
        "intake_status": intake.get("result_status"),
        "template_id": intake.get("template_id"),
        "downstream_agent": selected_agent,
        "revalidation_id": reval_id,
        "package_dir": str(package_dir),
        "acom_intake_path": str(intake_path),
        "structured_result_path": intake.get("result_json"),
        "source_handoff_path": str(source_handoff),
        "run_id": run_id,
        "gate_id": gate_id,
        "handoff_id": handoff_id,
        "run_record_path": str(run_path),
        "gate_path": str(gate_path),
        "handoff_path": str(handoff_path),
        "handoff_in_rel": f"handoffs/{source_handoff.name}",
        "handoff_out_rel": f"handoffs/{handoff_path.name}",
        "gate_decision": "PENDING_REVALIDATION",
        "automatic_execution_performed": False,
        "codex_summary_is_final_evidence": False,
        "accepted_as_final_evidence": False,
        "solver_run": False,
        "queue_runner_launched": False,
        "odb_opened": False,
        "profile": {
            "downstream_agent": profile.downstream_agent,
            "run_name": profile.run_name,
            "risk_level": profile.risk_level,
            "next_agent": profile.next_agent,
            "checklist": list(profile.checklist),
            "expected_outputs": list(profile.expected_outputs),
        },
        "forbidden_actions": [
            "Codex CLI call",
            "solver run",
            "QueueRunner launch",
            "ODB direct open",
            "automatic downstream agent execution",
            "automatic scheduling",
            "evidence approval",
        ],
    }
    valid, errors = validate_revalidation_scaffold(scaffold)
    if not valid:
        return _blocked(task, "REVALIDATION_REVIEW_REQUIRED", errors, intake)

    (package_dir / "REVALIDATION_PLAN.md").write_text(render_revalidation_plan(scaffold), encoding="utf-8")
    (package_dir / "REVALIDATION_INPUTS.md").write_text(render_revalidation_inputs(scaffold), encoding="utf-8")
    (package_dir / "REVALIDATION_CHECKLIST.md").write_text(render_revalidation_checklist(scaffold), encoding="utf-8")
    (package_dir / "REVALIDATION_EXPECTED_OUTPUTS.md").write_text(render_expected_outputs(scaffold), encoding="utf-8")
    (package_dir / "REVALIDATION_SCAFFOLD.json").write_text(json.dumps(scaffold, indent=2, ensure_ascii=False), encoding="utf-8")
    (package_dir / "REVALIDATION_REPORT.md").write_text(render_scaffold_report(scaffold), encoding="utf-8")
    run_path.write_text(render_run_record(scaffold), encoding="utf-8")
    gate_path.write_text(render_gate_record(scaffold), encoding="utf-8")
    handoff_path.write_text(render_handoff_record(scaffold), encoding="utf-8")

    protocol = validate_task_protocol(task)
    if not protocol["success"]:
        scaffold["status"] = "REVALIDATION_SCAFFOLD_BLOCKED_PROTOCOL_INVALID"
        scaffold["protocol_errors"] = protocol.get("errors", [])
        (package_dir / "REVALIDATION_SCAFFOLD.json").write_text(json.dumps(scaffold, indent=2, ensure_ascii=False), encoding="utf-8")
        return _result(task, scaffold, False, protocol.get("errors", []), protocol)
    return _result(task, scaffold, True, [], protocol)


def report_acom_revalidation(task_dir: str | Path, downstream_agent: str | None = None, revalidation_id: str | None = None) -> dict[str, Any]:
    task = Path(task_dir)
    root = task / "revalidation"
    candidates = []
    if root.exists():
        for path in root.glob("*_*/REVALIDATION_SCAFFOLD.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if downstream_agent and payload.get("downstream_agent") != downstream_agent:
                continue
            if revalidation_id and payload.get("revalidation_id") != revalidation_id:
                continue
            candidates.append((path.stat().st_mtime, path, payload))
    if not candidates:
        return {
            "command": "report-acom-revalidation",
            "verdict": "ACOM_REVALIDATION_REPORT_MISSING",
            "success": False,
            "errors": ["missing revalidation scaffold"],
            "warnings": [],
            "details": {"task_dir": str(task)},
        }
    _mtime, scaffold_path, scaffold = sorted(candidates, reverse=True)[0]
    report_path = task / "ACOM_REVALIDATION_REPORT.md"
    protocol_report = generate_protocol_report(task)
    report_path.write_text(
        render_scaffold_report(scaffold)
        + "\n## Pipeline Protocol\n"
        + f"- validation: `{protocol_report.get('validation_verdict')}`\n"
        + f"- protocol_report: `{protocol_report.get('report_path')}`\n",
        encoding="utf-8",
    )
    return {
        "command": "report-acom-revalidation",
        "verdict": "ACOM_REVALIDATION_REPORT_READY",
        "success": True,
        "errors": [],
        "warnings": [],
        "output_paths": {"report_path": str(report_path), "scaffold_json": str(scaffold_path)},
        "details": scaffold | {"protocol_validation": protocol_report.get("validation_verdict")},
    }


def _blocked(task: Path, status: str, errors: list[str], intake: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "command": "scaffold-acom-revalidation",
        "verdict": status,
        "success": False,
        "errors": errors,
        "warnings": [],
        "output_paths": {},
        "details": {
            "task_dir": str(task),
            "status": status,
            "intake_status": (intake or {}).get("result_status"),
            "downstream_agent": (intake or {}).get("downstream_agent"),
            "automatic_execution_performed": False,
            "gate_decision": "BLOCKED",
        },
    }


def _result(task: Path, scaffold: dict[str, Any], success: bool, errors: list[str], protocol: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": "scaffold-acom-revalidation",
        "verdict": scaffold["status"],
        "success": success,
        "errors": errors,
        "warnings": [],
        "output_paths": {
            "package_dir": scaffold.get("package_dir"),
            "run_record": scaffold.get("run_record_path"),
            "gate": scaffold.get("gate_path"),
            "handoff": scaffold.get("handoff_path"),
        },
        "details": scaffold | {"protocol_validation": protocol.get("verdict")},
    }


def _next_available_id(directory: Path, prefix: str, start: int) -> str:
    number = start
    while any(directory.glob(f"{prefix}_{number:03d}_*.md")):
        number += 1
    return f"{prefix}_{number:03d}"


def _agent_token(agent: str) -> str:
    token = agent
    append_agent = token.endswith("Agent")
    if token.endswith("Agent"):
        token = token[: -len("Agent")]
    chars: list[str] = []
    for index, ch in enumerate(token):
        if index and ch.isupper() and (not token[index - 1].isupper()):
            chars.append("_")
        chars.append(ch.upper())
    normalized = "".join(chars).replace("Q_A", "QA").replace("O_D_B", "ODB")
    return normalized + "_AGENT" if append_agent else normalized
