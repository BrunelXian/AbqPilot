from __future__ import annotations


WORKFLOW_PRESETS = [
    {
        "preset_id": "prepare_only",
        "display_name": "Prepare Only",
        "actions": ["run_prepare_pipeline"],
        "description": "Prepare audited INP and queue-preview artifacts without solver execution.",
    },
    {
        "preset_id": "approval_queue_only",
        "display_name": "Approval + Queue Only",
        "actions": ["create_approval_token", "poll_jobpilot_status"],
        "description": "Review approval state and queue/status artifacts. Real enqueue remains separately gated.",
    },
    {
        "preset_id": "status_poll_only",
        "display_name": "Status Poll Only",
        "actions": ["poll_jobpilot_status"],
        "description": "Read abqjobpilot status and output metadata only.",
    },
    {
        "preset_id": "completed_output_intake",
        "display_name": "Completed Output Intake",
        "actions": ["continue_from_job_output"],
        "description": "Validate existing completed job output evidence.",
    },
    {
        "preset_id": "analysis_repair_plan",
        "display_name": "Analysis / Repair Plan",
        "actions": ["generate_repair_plan"],
        "description": "Generate deterministic evaluation and repair-plan artifacts.",
    },
    {
        "preset_id": "report_export",
        "display_name": "Report Export",
        "actions": ["export_run_report"],
        "description": "Export task report artifacts.",
    },
]


def workflow_presets() -> list[dict]:
    return [dict(item) for item in WORKFLOW_PRESETS]
