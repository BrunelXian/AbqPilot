import json

from abqpilot import cli
from abqpilot.core.approval import (
    APPROVAL_PHRASE,
    approval_request_path,
    create_approval_request,
    create_approval_token,
    validate_approval_token,
    write_authorization_artifacts,
)


def test_cli_approve_jobpilot_enqueue_requires_exact_phrase(tmp_path):
    task_dir, request = _task_with_request(tmp_path)
    write_authorization_artifacts(task_dir / "steps" / "05_jobpilot_enqueue_authorization", request, {
        "status": "APPROVAL_TOKEN_MISSING",
        "approval_token_path": None,
        "errors": [],
        "warnings": [],
    })

    result = cli.command_approve_jobpilot_enqueue(task_dir, "human", "WRONG", 24)

    assert result["verdict"] == "APPROVAL_TOKEN_INVALID"
    assert result["success"] is False


def test_valid_token_validates_successfully(tmp_path):
    task_dir, request = _task_with_request(tmp_path)
    write_authorization_artifacts(task_dir / "steps" / "05_jobpilot_enqueue_authorization", request, {
        "status": "APPROVAL_TOKEN_MISSING",
        "approval_token_path": None,
        "errors": [],
        "warnings": [],
    })

    token = create_approval_token(task_dir, "human", APPROVAL_PHRASE, 24)
    validation = validate_approval_token(request, token["approval_token_path"])

    assert token["status"] == "APPROVAL_TOKEN_CREATED"
    assert validation["status"] == "APPROVAL_TOKEN_VALID"


def test_expired_token_is_rejected(tmp_path):
    task_dir, request = _task_with_request(tmp_path)
    write_authorization_artifacts(task_dir / "steps" / "05_jobpilot_enqueue_authorization", request, {
        "status": "APPROVAL_TOKEN_MISSING",
        "approval_token_path": None,
        "errors": [],
        "warnings": [],
    })

    token = create_approval_token(task_dir, "human", APPROVAL_PHRASE, -1)
    validation = validate_approval_token(request, token["approval_token_path"])

    assert validation["status"] == "APPROVAL_TOKEN_EXPIRED"


def test_hash_mismatch_is_rejected(tmp_path):
    task_dir, request = _task_with_request(tmp_path)
    write_authorization_artifacts(task_dir / "steps" / "05_jobpilot_enqueue_authorization", request, {
        "status": "APPROVAL_TOKEN_MISSING",
        "approval_token_path": None,
        "errors": [],
        "warnings": [],
    })
    token = create_approval_token(task_dir, "human", APPROVAL_PHRASE, 24)
    request["dry_run_result_sha256"] = "mismatch"

    validation = validate_approval_token(request, token["approval_token_path"])

    assert validation["status"] == "APPROVAL_HASH_MISMATCH"


def test_unsafe_condition_is_rejected(tmp_path):
    task_dir, request = _task_with_request(tmp_path, runtime_mutation_detected=True)
    write_authorization_artifacts(task_dir / "steps" / "05_jobpilot_enqueue_authorization", request, {
        "status": "APPROVAL_TOKEN_MISSING",
        "approval_token_path": None,
        "errors": [],
        "warnings": [],
    })

    token = create_approval_token(task_dir, "human", APPROVAL_PHRASE, 24)

    assert token["status"] == "APPROVAL_UNSAFE_CONDITIONS"


def _task_with_request(tmp_path, runtime_mutation_detected=False):
    task_dir = tmp_path / "task"
    step_dir = task_dir / "steps" / "05_jobpilot_enqueue_authorization"
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir(parents=True)
    candidate = evidence_dir / "generated_power_x2.inp"
    job_request = evidence_dir / "abqjobpilot_job_request.json"
    preflight = evidence_dir / "abqjobpilot_preflight_result.json"
    dry_run = evidence_dir / "abqjobpilot_dry_run_enqueue_result.json"
    candidate.write_text("*Heading\n", encoding="utf-8")
    job_request.write_text(
        json.dumps({"submission_mode": "preview_only", "allow_solver_submit": False, "inp_path": str(candidate)}),
        encoding="utf-8",
    )
    preflight.write_text(json.dumps({"status": "PREVIEW_READY"}), encoding="utf-8")
    dry_run.write_text(
        json.dumps({"status": "DRY_RUN_READY", "runtime_mutation_detected": runtime_mutation_detected}),
        encoding="utf-8",
    )
    request = create_approval_request(
        task_id="approval_task",
        step_dir=step_dir,
        candidate_inp_path=candidate,
        job_request_path=job_request,
        preflight_result_path=preflight,
        dry_run_result_path=dry_run,
    )
    approval_request_path(task_dir).parent.mkdir(parents=True, exist_ok=True)
    approval_request_path(task_dir).write_text(json.dumps(request, indent=2), encoding="utf-8")
    return task_dir, request
