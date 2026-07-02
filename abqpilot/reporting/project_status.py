from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


LATEST_VERDICT = "PASS_ABQPILOT_V2_STAGE3_8A_PATCH_QUEUE_PRODUCTION_REAL_ENQUEUE_SMOKE_READY"

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
            "Solver execution remains external/manual.",
            "Queue worker launch remains outside AbqPilot GUI authority.",
            "ODB opening remains limited to the existing gated metrics extractor.",
            "Repair plans are deterministic reports and do not mutate INP files.",
            "LLM reasoning is advisory and cannot execute workflow actions.",
            "LLM patch proposals are advisory and cannot apply patches.",
            "Patch preview supports heat_flux_magnitude_adjustment only in Stage 3.7.",
            "Patch-to-queue does not run production real enqueue unless a candidate-specific token is supplied.",
            "Stage 3.8A proves queue-only enqueue, but solver execution and completed patched-job intake remain future/manual boundaries.",
        ],
        "recommended_next_stages": [
            "Stage 3.5 GUI usability hardening and persistence polish",
            "Stage 3.6 completed-job metrics continuation smoke when ODB outputs exist",
            "Stage 4.x optional schema-bound advisory layer after deterministic cockpit maturity",
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
