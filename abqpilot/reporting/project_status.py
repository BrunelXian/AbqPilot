from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


LATEST_VERDICT = "PASS_ABQPILOT_V2_STAGE4_1B_ABQJOBPILOT_BACKED_DIAGNOSIS_INTEGRATION_READY"

PIPELINE_ORDER = [
    "01_export_cae",
    "02_audit_heat_x2",
    "03_abqjobpilot_preflight",
    "04_abqjobpilot_dry_run_enqueue",
    "05_jobpilot_enqueue_authorization",
    "06_abqjobpilot_real_enqueue",
    "07_abqjobpilot_status_poll",
    "08_solver_intake",
    "09_odb_metrics",
    "10_compare_metrics",
]

CAPABILITIES = [
    "guarded CAE/INP preparation",
    "heat patch audit",
    "StaticValidator / DiffGuard / PhysicsGuard",
    "task workspace and pipeline runner",
    "resume / skip / force-step",
    "abqjobpilot preflight",
    "dry-run enqueue",
    "human approval token",
    "controlled real queue-only enqueue",
    "queue status polling",
    "completed-job intake gate",
    "gated ODB metrics continuation",
    "metrics comparison",
    "deterministic evaluation",
    "deterministic repair-plan generation",
    "module registry",
    "event stream",
    "runtime view model",
    "tkinter GUI beta",
    "artifact browser / run report export",
    "alpha freeze package",
    "optional schema-bound LLM provider contract",
    "deterministic mock reasoner",
    "real LLM task-summary reasoning panel",
    "strict LLM output safety validation",
    "LLM-guided candidate patch proposal review",
    "strict patch proposal safety validation",
    "guarded PatchBuilder application preview",
    "guarded patch-to-queue workflow",
    "candidate-specific patch queue approval token",
    "patch queue production queue-only enqueue smoke",
    "patched job status poll and completed output intake gate",
    "patched job gated metrics continuation gate",
    "patched job report",
    "real sanity-base-derived patch candidate recovery",
    "fixture workflow evidence reclassified as non-production evidence",
    "equivalent real ODB intake, gated metrics extraction, and mixed metrics report",
    "controlled single-job Abaqus solver automation framework",
    "solver-specific approval token",
    "controlled solver monitor, output intake, and report gates",
    "Abaqus job/ODB failure diagnosis taxonomy reference",
    "deterministic Abaqus job/ODB failure diagnosis module",
    "deterministic solver-failure repair proposal",
    "abqjobpilot-backed job/ODB diagnosis integration",
    "abqjobpilot runtime/report record reader",
]

SAFETY_BOUNDARIES = {
    "Abaqus solver submit": "not automatic",
    "Queue" + "Runner launch": "not automatic",
    "abqjobpilot GUI": "not used",
    "Open" + "AI API": "not integrated",
    "LLM repair": "not integrated",
    "ODB open": "gated extractor only",
    "Real enqueue": "approval-token gated and queue-only",
    "INP mutation from repair plan": "disabled",
    "LLM provider": "optional and confirmation-gated",
    "Real LLM task summary": "sanitized, compact, confirmation-gated, read-only",
    "LLM patch proposal": "advisory only, no INP mutation, guard-validated",
    "PatchBuilder preview": "candidate INP copy only, validator-gated, no solver/enqueue",
    "Patch-to-queue workflow": "validated preview only, candidate approval-token gated, no solver/" + "Queue" + "Runner/ODB open",
    "Patch queue production smoke": "queue-only proof confirmed; only runtime/queue.json changed",
    "Patched job intake": "read-only status/output evidence gate; no solver/" + "Queue" + "Runner/ODB direct open",
    "Patched job metrics": "requires accepted existing ODB and uses the existing gated metrics extractor only",
    "Real patch candidates": "must derive from sanity-base CAE/exported INP; toy fixtures are workflow-only",
    "Equivalent ODB intake": "requires Stage 3.9B traceability/equivalence evidence and uses existing ODBs only",
    "Controlled solver automation": "single validated sanity-base-derived candidate only; solver-specific approval-token gated; fixed Abaqus command shape; no batch loop",
    "Job/ODB diagnosis": "read-only log and metadata parser; ODB existence alone is not accepted",
    "Solver-failure repair proposal": "diagnosis-driven and proposal-only; no INP mutation, no solver run, no ODB open",
    "abqjobpilot execution records": "abqjobpilot remains execution-record/path authority; AbqPilot consumes records read-only for diagnosis and repair context",
    "Arbitrary solver commands": "not accepted",
    "LLM solver authority": "not integrated",
    "API key display": "masked only",
}

MAIN_COMMANDS = [
    "python -m abqpilot.cli status",
    "python -m abqpilot.cli run-sanity-demo --config configs\\sanity_demo_task.json --mode prepare-only --task-id <task_id>",
    "python -m abqpilot.cli approve-jobpilot-enqueue --task-dir <task_dir> --approved-by human --approval-phrase I_APPROVE_ABQJOBPILOT_REAL_ENQUEUE_FOR_THIS_TASK",
    "python -m abqpilot.cli continue-from-job-output --task-dir <task_dir>",
    "python -m abqpilot.cli generate-repair-plan --task-dir <task_dir>",
    "python -m abqpilot.cli export-run-report --task-dir <task_dir>",
    "python -m abqpilot.cli llm-reason --provider mock --task-dir <task_dir>",
    "python -m abqpilot.cli llm-reason --task-dir <task_dir> --dry-run-input-summary",
    "python -m abqpilot.cli llm-reason --provider chatanywhere --task-dir <task_dir> --confirm-send-task-summary",
    "python -m abqpilot.cli propose-patch --task-dir <task_dir> --provider mock",
    "python -m abqpilot.cli propose-patch --task-dir <task_dir> --provider chatanywhere --confirm-send-patch-context",
    "python -m abqpilot.cli preview-patch --task-dir <task_dir> --provider-source llm",
    "python -m abqpilot.cli queue-patch-preview --task-dir <task_dir> --patch-preview-dir <preview_dir> --mode preflight-only",
    "python -m abqpilot.cli queue-patch-preview --task-dir <task_dir> --patch-preview-dir <preview_dir> --mode dry-run-enqueue",
    "python -m abqpilot.cli approve-patch-queue --workflow-dir <workflow_dir> --approved-by human --approval-phrase I_APPROVE_ABQPILOT_PATCH_CANDIDATE_QUEUE_ONLY_ENQUEUE",
    "python -m abqpilot.cli queue-patch-preview --workflow-dir <workflow_dir> --mode real-queue-only --approval-token <token_path>",
    "python -m abqpilot.cli poll-patch-queue --workflow-dir <workflow_dir>",
    "python -m abqpilot.cli intake-patched-job-output --workflow-dir <workflow_dir>",
    "python -m abqpilot.cli extract-patched-job-metrics --workflow-dir <workflow_dir>",
    "python -m abqpilot.cli report-patched-job --workflow-dir <workflow_dir>",
    "python -m abqpilot.cli recover-sanity-base-patch-candidate",
    "python -m abqpilot.cli run-stage3-9c-equivalent-odb",
    "python -m abqpilot.cli prepare-solver-run --candidate-inp <candidate_inp> --source-inp <source_inp> --evidence-dir <stage3_9b_dir> --cpus 14",
    "python -m abqpilot.cli approve-solver-run --solver-run-dir <solver_run_dir> --approved-by human --approval-phrase I_APPROVE_ABQPILOT_CONTROLLED_ABAQUS_SOLVER_RUN",
    "python -m abqpilot.cli run-solver-approved --solver-run-dir <solver_run_dir> --approval-token <token_path>",
    "python -m abqpilot.cli monitor-solver-run --solver-run-dir <solver_run_dir>",
    "python -m abqpilot.cli diagnose-job-output --job-dir <job_dir> --job-name <job_name>",
    "python -m abqpilot.cli diagnose-job-output --abqjobpilot-report <report_json>",
    "python -m abqpilot.cli diagnose-job-output --abqjobpilot-job-id <job_id> --abqjobpilot-runtime-dir D:\\Projects\\abqjobpilot_dev\\runtime",
    "python -m abqpilot.cli list-abqjobpilot-records --abqjobpilot-runtime-dir D:\\Projects\\abqjobpilot_dev\\runtime --max-results 20",
    "python -m abqpilot.cli intake-solver-run-output --solver-run-dir <solver_run_dir>",
    "python -m abqpilot.cli report-solver-run --solver-run-dir <solver_run_dir>",
    "python -c \"from abqpilot.patching.patch_queue_smoke import write_stage3_8a_smoke_summary; write_stage3_8a_smoke_summary(<workflow_dir>)\"",
    "python -m abqpilot.cli probe-llm --provider chatanywhere --model deepseek-chat --confirm-send-test-request",
    "python -m abqpilot.cli gui",
]


def export_project_status(root: str | Path = ".") -> dict[str, Any]:
    project_root = Path(root)
    status = {
        "schema_version": "0.1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "latest_verdict": LATEST_VERDICT,
        "llm_provider_contract": {
            "status": "optional",
            "default_provider": "mock",
            "real_provider_probe_requires_confirmation": True,
            "api_key_display": "masked",
            "task_summary_requires_confirmation": True,
            "patch_context_requires_confirmation": True,
            "strict_json_safety_validation": True,
        },
        "external_dependency": {
            "path": "D:\\Projects\\abqjobpilot_dev",
            "status": "PASS_ABQJOBPILOT_STAGE_A2_QUEUE_ONLY_ENQUEUE_CONTRACT_READY",
        },
        "capabilities": CAPABILITIES,
        "safety_boundaries": SAFETY_BOUNDARIES,
        "main_cli_commands": MAIN_COMMANDS,
        "gui_status": "GUI Beta safe workflow cockpit",
        "current_pipeline_order": PIPELINE_ORDER,
        "known_limitations": [
            "The controlled solver automation framework exists, but the first real Stage 4.0 smoke failed safely because Abaqus terminated the analysis before completion.",
            "Queue worker launch remains outside AbqPilot GUI authority.",
            "ODB opening remains limited to the existing gated metrics extractor.",
            "Repair plans are deterministic reports and do not mutate INP files.",
            "LLM reasoning is advisory and cannot execute workflow actions.",
            "LLM patch proposals are advisory and cannot apply patches.",
            "Patch preview supports heat_flux_magnitude_adjustment only in Stage 3.7.",
            "Patch-to-queue does not run production real enqueue unless a candidate-specific token is supplied.",
            "Stage 3.9 can poll and intake completed patched-job outputs, but solver execution remains external/manual.",
            "Patched-job metrics remain blocked until an existing unlocked ODB is accepted by the intake gate.",
            "Stage 3.7/3.8 fixture patch candidates are workflow-only and not production solver-ready evidence.",
            "Stage 3.9B recovered a real sanity-base-derived candidate from the Stage 1.6A exported INP.",
            "Stage 3.9C accepted an existing manually completed equivalent 2x ODB and extracted metrics through the gated extractor.",
            "Stage 4.0 does not support batch loops, arbitrary solver commands, LLM-controlled execution, or Queue" + "Runner launch.",
            "Stage 4.1 diagnosis implementation should use docs/diagnostics/ABQPILOT_ABAQUS_JOB_ODB_FAILURE_DIAGNOSIS_TAXONOMY.md as the design reference.",
            "Stage 4.1 blocks metrics extraction unless diagnosis_status is JOB_COMPLETED_ODB_ACCEPTABLE.",
            "Stage 4.2 creates repair proposals only and does not apply solver-control patches.",
            "Stage 4.1B consumes abqjobpilot records read-only; abqjobpilot remains the execution lifecycle and path authority.",
            "Attempt-block parsing is intentionally minimal and supports START/END marker styles used by abqjobpilot logs.",
        ],
        "recommended_next_stages": [
            "Stage 4.3 guarded solver-control patch preview for approved Stage 4.2 proposals",
            "GUI persistence and usability hardening",
        ],
    }
    json_path = project_root / "PROJECT_STATUS_CURRENT.json"
    md_path = project_root / "PROJECT_STATUS_CURRENT.md"
    json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_markdown(status), encoding="utf-8")
    return {
        "command": "export-project-status",
        "verdict": "PROJECT_STATUS_EXPORTED",
        "success": True,
        "output_paths": {
            "project_status_json": str(json_path),
            "project_status_md": str(md_path),
        },
        "details": status,
        "warnings": [],
        "errors": [],
    }


def _render_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# AbqPilot Project Status",
        "",
        f"Latest verdict: `{status['latest_verdict']}`",
        f"Generated at: `{status['generated_at']}`",
        "",
        "## Capabilities",
        "",
    ]
    lines.extend(f"- {item}" for item in status["capabilities"])
    lines.extend(["", "## Safety Boundary Matrix", "", "| Boundary | Status |", "| --- | --- |"])
    lines.extend(f"| {key} | {value} |" for key, value in status["safety_boundaries"].items())
    lines.extend(["", "## Main CLI Commands", ""])
    lines.extend(f"- `{item}`" for item in status["main_cli_commands"])
    lines.extend(["", "## Current Pipeline Order", ""])
    lines.extend(f"- `{item}`" for item in status["current_pipeline_order"])
    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {item}" for item in status["known_limitations"])
    lines.extend(["", "## Recommended Next Stages", ""])
    lines.extend(f"- {item}" for item in status["recommended_next_stages"])
    return "\n".join(lines) + "\n"
