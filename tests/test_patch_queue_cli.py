import json
from pathlib import Path

from abqpilot import cli
from abqpilot.patching.patch_queue_workflow import PATCH_QUEUE_APPROVAL_PHRASE


def test_parser_accepts_queue_patch_preview():
    args = cli.build_parser().parse_args(["queue-patch-preview", "--task-dir", "task", "--mode", "dry-run-enqueue"])

    assert args.command == "queue-patch-preview"
    assert args.mode == "dry-run-enqueue"


def test_parser_accepts_approve_patch_queue():
    args = cli.build_parser().parse_args(
        [
            "approve-patch-queue",
            "--workflow-dir",
            "workflow",
            "--approved-by",
            "human",
            "--approval-phrase",
            PATCH_QUEUE_APPROVAL_PHRASE,
        ]
    )

    assert args.command == "approve-patch-queue"


def test_parser_accepts_poll_patch_queue():
    args = cli.build_parser().parse_args(["poll-patch-queue", "--workflow-dir", "workflow"])

    assert args.command == "poll-patch-queue"


def test_cli_queue_patch_preflight_only(monkeypatch, tmp_path):
    task, preview = _preview(tmp_path)
    _patch_adapter(monkeypatch)

    result = cli.command_queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="preflight-only")

    assert result["verdict"] == "PATCH_QUEUE_PREFLIGHT_READY"
    assert result["details"]["dry_run_enqueue_status"] == "NOT_RUN"


def test_cli_queue_patch_dry_run(monkeypatch, tmp_path):
    task, preview = _preview(tmp_path)
    _patch_adapter(monkeypatch)

    result = cli.command_queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="dry-run-enqueue")

    assert result["verdict"] == "PATCH_QUEUE_DRY_RUN_READY"
    workflow = Path(result["output_paths"]["artifact_dir"])
    token = cli.command_approve_patch_queue(workflow, "human", PATCH_QUEUE_APPROVAL_PHRASE)
    assert token["verdict"] == "APPROVAL_TOKEN_CREATED"


def test_cli_real_queue_only_mocked(monkeypatch, tmp_path):
    task, preview = _preview(tmp_path)
    _patch_adapter(monkeypatch)
    dry = cli.command_queue_patch_preview(task_dir=task, patch_preview_dir=preview, mode="dry-run-enqueue")
    workflow = Path(dry["output_paths"]["artifact_dir"])
    token = cli.command_approve_patch_queue(workflow, "human", PATCH_QUEUE_APPROVAL_PHRASE)

    result = cli.command_queue_patch_preview(workflow_dir=workflow, mode="real-queue-only", approval_token=token["output_paths"]["approval_token_json"])

    assert result["verdict"] == "PATCH_QUEUE_REAL_ENQUEUE_COMPLETED"


def _patch_adapter(monkeypatch):
    class FakeAdapter:
        def __init__(self, project_root=None):
            self.project_root = project_root

        def build_request(self, inp_path, job_name, cpus, batch, strategy, working_dir=None, metadata=None):
            return {
                "inp_path": str(inp_path),
                "job_name": job_name,
                "cpus": cpus,
                "batch": batch,
                "strategy": strategy,
                "working_dir": working_dir,
                "submission_mode": "preview_only",
                "allow_solver_submit": False,
                "metadata": metadata or {},
            }

        def preflight(self, request):
            return {"status": "PREVIEW_READY", "job_id": request["job_name"], "command_preview": "preview", "errors": [], "warnings": []}

        def dry_run_enqueue(self, request):
            return {
                "status": "DRY_RUN_READY",
                "job_id": request["job_name"],
                "runtime_mutation_detected": False,
                "queue_only": True,
                "errors": [],
                "warnings": [],
            }

        def real_enqueue(self, request, approval_report):
            return {
                "status": "REAL_ENQUEUE_COMPLETED",
                "job_id": "q_patch",
                "queue_mutated": True,
                "forbidden_mutation_detected": False,
                "errors": [],
                "warnings": [],
            }

    monkeypatch.setattr("abqpilot.patching.patch_queue_workflow.AbqJobPilotPreflightAdapter", FakeAdapter)


def _preview(tmp_path):
    task = tmp_path / "task"
    preview = task / "patch_previews" / "preview_001"
    preview.mkdir(parents=True)
    source = tmp_path / "source.inp"
    candidate = tmp_path / "candidate.inp"
    source.write_text("*Heading\n", encoding="utf-8")
    candidate.write_text("*Heading\n** patched\n", encoding="utf-8")
    summary = {
        "preview_status": "PATCH_PREVIEW_READY",
        "patch_type": "heat_flux_magnitude_adjustment",
        "source_inp_path": str(source),
        "candidate_inp_path": str(candidate),
        "changed_lines_count": 1,
        "unrelated_changes_count": 0,
        "static_validator_status": "PASS",
        "diff_guard_status": "PASS",
        "physics_guard_status": "PASS",
        "solver_submitted": False,
        "job_enqueued": False,
        "requires_human_review": True,
    }
    (preview / "patch_preview_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return task, preview
