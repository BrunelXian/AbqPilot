from __future__ import annotations

from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RUNS = (
    ("RUN_001", "INTAKE", "IntakeAgent", "LOW"),
    ("RUN_002", "AUDIT", "AuditAgent", "LOW"),
    ("RUN_003", "CANDIDATE_BUILD", "CandidateBuilderAgent", "MEDIUM"),
    ("RUN_004", "GUARD_VALIDATION", "GuardAgent", "HIGH"),
    ("RUN_005", "EXECUTION", "ExecutionAgent", "HIGH"),
    ("RUN_006", "DIAGNOSIS", "DiagnosisAgent", "HIGH"),
    ("RUN_007", "METRICS", "MetricsAgent", "HIGH"),
    ("RUN_008", "EVIDENCE_REPORT", "EvidenceReportAgent", "MEDIUM"),
)

HANDOFFS = (
    ("HANDOFF_001", "INTAKE_TO_AUDIT", "IntakeAgent", "AuditAgent", "RUN_001", "RUN_002", "LOW"),
    ("HANDOFF_002", "AUDIT_TO_CANDIDATE_BUILDER", "AuditAgent", "CandidateBuilderAgent", "RUN_002", "RUN_003", "MEDIUM"),
    ("HANDOFF_003", "CANDIDATE_BUILDER_TO_GUARD", "CandidateBuilderAgent", "GuardAgent", "RUN_003", "RUN_004", "MEDIUM"),
    ("HANDOFF_004", "GUARD_TO_EXECUTION", "GuardAgent", "ExecutionAgent", "RUN_004", "RUN_005", "HIGH"),
    ("HANDOFF_005", "EXECUTION_TO_DIAGNOSIS", "ExecutionAgent", "DiagnosisAgent", "RUN_005", "RUN_006", "HIGH"),
    ("HANDOFF_006", "DIAGNOSIS_TO_METRICS", "DiagnosisAgent", "MetricsAgent", "RUN_006", "RUN_007", "HIGH"),
    ("HANDOFF_007", "METRICS_TO_EVIDENCE_REPORT", "MetricsAgent", "EvidenceReportAgent", "RUN_007", "RUN_008", "MEDIUM"),
)

GATES = (
    ("GATE_001", "ALLOW_CANDIDATE_BUILD", "AUDIT_TO_CANDIDATE_BUILD", "MEDIUM"),
    ("GATE_002", "ALLOW_EXECUTION", "GUARD_VALIDATION_TO_EXECUTION", "HIGH"),
    ("GATE_003", "ACCEPT_ODB_FOR_METRICS", "DIAGNOSIS_TO_METRICS", "HIGH"),
    ("GATE_004", "FREEZE_FINAL_EVIDENCE", "EVIDENCE_REPORT_TO_FINAL_VERDICT", "HIGH"),
)


def scaffold_pipeline_task(task_id: str, root: str | Path | None = None, overwrite: bool = False) -> dict[str, Any]:
    base = Path(root) if root is not None else PROJECT_ROOT
    task_dir = base / "runs" / "tasks" / task_id
    created: list[str] = []
    for directory in (task_dir / "trace", task_dir / "handoffs", task_dir / "gates", task_dir / "artifacts"):
        directory.mkdir(parents=True, exist_ok=True)
    for run_id, run_name, _agent, _risk in RUNS:
        artifact_dir = task_dir / "artifacts" / f"{run_id.lower()}_{run_name.lower()}"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        created.append(str(artifact_dir))
    files = {
        task_dir / "TASK_PLAN.md": _task_plan(task_id),
        task_dir / "TRACE_INDEX.md": _trace_index(task_id),
        task_dir / "TASK_FINAL_EVIDENCE_LEDGER.md": _final_ledger(task_id),
    }
    for index, (run_id, run_name, agent, risk) in enumerate(RUNS, start=1):
        files[task_dir / "trace" / f"{run_id}_{run_name}.md"] = _run_report(task_id, run_id, run_name, agent, risk, index)
    for handoff_id, name, from_agent, to_agent, from_run, target_run, risk in HANDOFFS:
        files[task_dir / "handoffs" / f"{handoff_id}_{name}.md"] = _handoff(task_id, handoff_id, name, from_agent, to_agent, from_run, target_run, risk)
    for gate_id, name, transition, risk in GATES:
        files[task_dir / "gates" / f"{gate_id}_{name}.md"] = _gate(task_id, gate_id, transition, risk)
    for path, text in files.items():
        if path.exists() and not overwrite:
            continue
        path.write_text(text, encoding="utf-8")
        created.append(str(path))
    return {
        "verdict": "PIPELINE_TASK_SCAFFOLD_CREATED",
        "success": True,
        "task_id": task_id,
        "task_dir": str(task_dir),
        "created_paths": created,
    }


def _task_plan(task_id: str) -> str:
    return f"""---
doc_type: task_plan
task_id: {task_id}
status: DRAFT
risk_level: LOW
---

# Task Plan

## Purpose
Define the bounded pipeline task objective.

## Pipeline Scope
Pipeline-style multi-agent workflow with gated high-risk transitions.

## Inputs
List input artifacts and upstream approvals.

## Risk Level
LOW until a gate raises the transition risk.
"""


def _trace_index(task_id: str) -> str:
    run_lines = "\n".join(f"- trace/{run_id}_{name}.md" for run_id, name, _agent, _risk in RUNS)
    handoff_lines = "\n".join(f"- handoffs/{handoff_id}_{name}.md" for handoff_id, name, *_rest in HANDOFFS)
    gate_lines = "\n".join(f"- gates/{gate_id}_{name}.md" for gate_id, name, *_rest in GATES)
    return f"""---
doc_type: trace_index
task_id: {task_id}
status: DRAFT
---

# Trace Index

## Runs
{run_lines}

## Handoffs
{handoff_lines}

## Gates
{gate_lines}

## Artifact Directories
- artifacts/run_001_intake through artifacts/run_008_evidence_report
"""


def _run_report(task_id: str, run_id: str, run_name: str, agent: str, risk: str, index: int) -> str:
    handoff_in = "none" if index == 1 else f"handoffs/{HANDOFFS[index - 2][0]}_{HANDOFFS[index - 2][1]}.md"
    handoff_out = "none" if index > len(HANDOFFS) else f"handoffs/{HANDOFFS[index - 1][0]}_{HANDOFFS[index - 1][1]}.md"
    return f"""---
doc_type: run_report
task_id: {task_id}
run_id: {run_id}
run_name: {run_name}
agent: {agent}
status: PENDING
risk_level: {risk}
handoff_in: {handoff_in}
handoff_out: {handoff_out}
gate_required_next: false
next_recommended_stage: TBD
forbidden_actions:
  solver_run: false
  queue_runner_launched: false
  odb_opened: false
  source_cae_mutated: false
  source_inp_mutated: false
  env_read: false
  shell_true_used: false
---

# {run_id} {run_name}

## Purpose

## Inputs

## Actions Taken

## Outputs

## Validation

## Guardrails / Forbidden Actions Confirmation

## Verdict

## Claim Boundary

## Next Recommended Step
"""


def _handoff(task_id: str, handoff_id: str, name: str, from_agent: str, to_agent: str, from_run: str, target_run: str, risk: str) -> str:
    target_suffix = next(run_name for run_id, run_name, *_rest in RUNS if run_id == target_run)
    return f"""---
doc_type: handoff
task_id: {task_id}
handoff_id: {handoff_id}
from_agent: {from_agent}
to_agent: {to_agent}
from_run: {from_run}
target_run: {target_run}
risk_level: {risk}
gate_required_before_receiver_execution: false
gate_required_after_receiver_completion: false
expected_output: trace/{target_run}_{target_suffix}.md
---

# {handoff_id} {name}

## Context

## Inputs for Receiver

## Required Task

## Allowed Actions

## Forbidden Actions

## Required Outputs

## Acceptance Criteria

## Gate Requirement
"""


def _gate(task_id: str, gate_id: str, transition: str, risk: str) -> str:
    return f"""---
doc_type: gate_decision
task_id: {task_id}
gate_id: {gate_id}
transition: {transition}
risk_level: {risk}
decision: PENDING
approver_type: HUMAN
human_approval_required: true
human_approval_token_valid: false
required_conditions_met: false
---

# {gate_id} {transition}

## Transition

## Risk Level

## Required Conditions

## Evidence Reviewed

## Decision

## Approver

## Reason

## Residual Risk
"""


def _final_ledger(task_id: str) -> str:
    return f"""---
doc_type: final_evidence_ledger
task_id: {task_id}
status: DRAFT
final_verdict: NOT_FROZEN
---

# Task Final Evidence Ledger

## Trace Inputs

## Handoff Inputs

## Gate Decisions

## Artifact Evidence

## Validator Evidence

## Diagnosis Evidence

## Metrics Evidence

## Known Limitations

## Final Verdict Recommendation
"""
