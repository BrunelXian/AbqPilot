import json
import sys
from pathlib import Path

from abqpilot import cli
from abqpilot.integrations import AbqJobPilotPreflightAdapter
from abqpilot.core.pipeline_runner import PipelineRunner
from abqpilot.core.pipeline_steps import STEP_NAMES


def test_real_enqueue_disabled_by_default_blocks_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))

    result = AbqJobPilotPreflightAdapter().real_enqueue(
        _request(tmp_path), _approval_report(allow_abqjobpilot_real_enqueue=False)
    )

    assert result["status"] == "REAL_ENQUEUE_REJECTED_CONFIG_DISABLED"
    assert calls == []


def test_real_enqueue_requires_valid_approval_token_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))
    report = _approval_report(approval_token_status="APPROVAL_TOKEN_MISSING")

    result = AbqJobPilotPreflightAdapter().real_enqueue(_request(tmp_path), report)

    assert result["status"] == "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE"
    assert calls == []


def test_expired_token_blocks_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))
    report = _approval_report(approval_token_status="APPROVAL_TOKEN_EXPIRED")

    result = AbqJobPilotPreflightAdapter().real_enqueue(_request(tmp_path), report)

    assert result["status"] == "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE"
    assert calls == []


def test_hash_mismatch_blocks_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))
    report = _approval_report(job_request_sha256_matches=False)

    result = AbqJobPilotPreflightAdapter().real_enqueue(_request(tmp_path), report)

    assert result["status"] == "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE"
    assert calls == []


def test_allow_solver_submit_true_blocks_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))
    request = _request(tmp_path)
    request["allow_solver_submit"] = True

    result = AbqJobPilotPreflightAdapter().real_enqueue(request, _approval_report())

    assert result["status"] == "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE"
    assert calls == []


def test_submission_mode_submit_blocks_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))
    request = _request(tmp_path)
    request["submission_mode"] = "submit"

    result = AbqJobPilotPreflightAdapter().real_enqueue(request, _approval_report())

    assert result["status"] == "REAL_ENQUEUE_BLOCKED_BY_AUTHORIZATION_GATE"
    assert calls == []


def test_missing_queue_only_proof_rejects_before_api_call(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", lambda _name: calls.append("import"))
    report = _approval_report(queue_only_confirmed=False, dry_run_result={})

    result = AbqJobPilotPreflightAdapter().real_enqueue(_request(tmp_path), report)

    assert result["status"] == "REAL_ENQUEUE_REJECTED_UNSAFE_DIRECT_SUBMIT"
    assert calls == []


def test_adapter_calls_public_api_enqueue_dry_run_false_after_gates_pass(tmp_path):
    _clear_abqjobpilot_modules()
    root = _write_fake_api(tmp_path, mutation="queue")
    request = _request(root / "work")
    adapter = AbqJobPilotPreflightAdapter(project_root=str(root))

    result = adapter.real_enqueue(request, _approval_report())

    assert result["status"] == "REAL_ENQUEUE_COMPLETED"
    assert result["queue_mutated"] is True
    assert result["forbidden_mutation_detected"] is False
    assert json.loads((root / "runtime" / "queue.json").read_text(encoding="utf-8")) == [{"dry_run": False}]


def test_live_status_mutation_is_rejected(tmp_path):
    _clear_abqjobpilot_modules()
    root = _write_fake_api(tmp_path, mutation="live_status")
    adapter = AbqJobPilotPreflightAdapter(project_root=str(root))

    result = adapter.real_enqueue(_request(root / "work"), _approval_report())

    assert result["status"] == "REAL_ENQUEUE_RUNTIME_MUTATION_UNSAFE"
    assert result["forbidden_mutation_detected"] is True


def test_reports_mutation_is_rejected(tmp_path):
    _clear_abqjobpilot_modules()
    root = _write_fake_api(tmp_path, mutation="reports")
    adapter = AbqJobPilotPreflightAdapter(project_root=str(root))

    result = adapter.real_enqueue(_request(root / "work"), _approval_report())

    assert result["status"] == "REAL_ENQUEUE_RUNTIME_MUTATION_UNSAFE"
    assert result["forbidden_mutation_detected"] is True


def test_pipeline_includes_real_enqueue_step():
    assert "06_abqjobpilot_real_enqueue" in STEP_NAMES


def test_pipeline_real_enqueue_writes_blocked_artifacts_when_config_disabled(tmp_path):
    runner = _runner_with_real_enqueue_evidence(tmp_path, allow_real=False)

    result = runner.run_step("06_abqjobpilot_real_enqueue")

    assert result["verdict"] == "REAL_ENQUEUE_REJECTED_CONFIG_DISABLED"
    assert Path(result["output_paths"]["abqjobpilot_real_enqueue_result"]).exists()


def test_skip_real_jobpilot_enqueue_skips_safely(tmp_path):
    runner = _runner_with_real_enqueue_evidence(tmp_path, allow_real=True, skip_real=True)

    result = runner.run_step("06_abqjobpilot_real_enqueue")

    assert result["verdict"] == "SKIPPED_REAL_JOBPILOT_ENQUEUE"
    assert result["success"] is True


def test_successful_real_enqueue_stops_before_solver_boundary(monkeypatch, tmp_path):
    runner = _runner_with_real_enqueue_evidence(tmp_path, allow_real=True, queue_only_confirmed=True)

    class FakeAdapter:
        def __init__(self, project_root=None):
            pass

        def real_enqueue(self, request, approval_report):
            return {
                "status": "REAL_ENQUEUE_COMPLETED",
                "queue_mutated": True,
                "forbidden_mutation_detected": False,
                "errors": [],
                "warnings": [],
            }

        def write_real_enqueue_artifacts(self, request, result, out_dir):
            out = Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            paths = {}
            for name in (
                "abqjobpilot_real_enqueue_request",
                "abqjobpilot_real_enqueue_result",
                "abqjobpilot_real_enqueue_safety_report",
                "abqjobpilot_real_enqueue_preview",
            ):
                path = out / f"{name}.json"
                path.write_text(json.dumps(result), encoding="utf-8")
                paths[name] = str(path)
            return paths

    monkeypatch.setattr("abqpilot.integrations.AbqJobPilotPreflightAdapter", FakeAdapter)
    _mark_previous_steps_completed(runner)

    result = runner.run_until("08_solver_intake")

    assert result["verdict"] == "REAL_ENQUEUE_COMPLETED"
    assert result["final_status"] == "WAITING_FOR_ABQJOBPILOT_OR_MANUAL_SOLVER"
    assert result["current_step"] == "06_abqjobpilot_real_enqueue"


def test_cli_parser_accepts_real_enqueue_flags():
    args = cli.build_parser().parse_args(
        [
            "run-sanity-demo",
            "--config",
            "configs/sanity_demo_task.json",
            "--allow-real-jobpilot-enqueue",
            "--skip-real-jobpilot-enqueue",
        ]
    )
    assert args.allow_real_jobpilot_enqueue is True
    assert args.skip_real_jobpilot_enqueue is True


def _request(tmp_path):
    work = Path(tmp_path)
    work.mkdir(parents=True, exist_ok=True)
    inp = work / "case.inp"
    inp.write_text("*Heading\n", encoding="utf-8")
    return {
        "inp_path": str(inp),
        "job_name": "case",
        "cpus": 14,
        "batch": "batch",
        "strategy": "strategy",
        "working_dir": str(work),
        "submission_mode": "preview_only",
        "allow_solver_submit": False,
        "metadata": {},
    }


def _approval_report(**overrides):
    report = {
        "allow_abqjobpilot_real_enqueue": True,
        "approval_token_status": "APPROVAL_TOKEN_VALID",
        "preflight_status": "PREVIEW_READY",
        "dry_run_enqueue_status": "DRY_RUN_READY",
        "runtime_mutation_detected": False,
        "allow_solver_submit": False,
        "submission_mode": "preview_only",
        "candidate_inp_sha256_matches": True,
        "job_request_sha256_matches": True,
        "preflight_result_sha256_matches": True,
        "dry_run_result_sha256_matches": True,
        "queue_only_confirmed": True,
        "dry_run_result": {"queue_only": True},
    }
    report.update(overrides)
    return report


def _mark_previous_steps_completed(runner):
    for step_name in (
        "01_export_cae",
        "02_audit_heat_x2",
        "03_abqjobpilot_preflight",
        "04_abqjobpilot_dry_run_enqueue",
        "05_jobpilot_enqueue_authorization",
    ):
        path = runner.workspace.step_result_path(step_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"command": step_name, "verdict": "PRESEEDED", "success": True}), encoding="utf-8")
        runner.workspace.mark_step_completed(step_name, "PRESEEDED", path)


def _write_fake_api(tmp_path, mutation):
    root = tmp_path / f"fake_abqjobpilot_{mutation}"
    api = root / "abqjobpilot" / "api"
    runtime = root / "runtime"
    reports = runtime / "reports"
    api.mkdir(parents=True)
    reports.mkdir(parents=True)
    (runtime / "queue.json").write_text("[]", encoding="utf-8")
    (runtime / "live_status.json").write_text("{}", encoding="utf-8")
    (root / "abqjobpilot" / "__init__.py").write_text("", encoding="utf-8")
    (api / "__init__.py").write_text(
        f"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
MUTATION = {mutation!r}

class JobRequest:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

class AbqJobPilotClient:
    def enqueue(self, request, dry_run=False):
        if dry_run is not False:
            raise AssertionError("real enqueue must call dry_run=False")
        runtime = ROOT / "runtime"
        if MUTATION == "queue":
            (runtime / "queue.json").write_text(json.dumps([{{"dry_run": dry_run}}]), encoding="utf-8")
        elif MUTATION == "live_status":
            (runtime / "live_status.json").write_text(json.dumps({{"changed": True}}), encoding="utf-8")
        elif MUTATION == "reports":
            (runtime / "reports" / "created.json").write_text("{{}}", encoding="utf-8")
        return {{"status": "QUEUE_ENQUEUED", "job_id": request.kwargs.get("job_name")}}
""",
        encoding="utf-8",
    )
    return root


def _runner_with_real_enqueue_evidence(tmp_path, allow_real, skip_real=False, queue_only_confirmed=False):
    from tests.test_jobpilot_authorization_gate import _runner_with_authorization_evidence

    runner = _runner_with_authorization_evidence(tmp_path, f"real_{allow_real}_{skip_real}_{queue_only_confirmed}")
    config = dict(runner.config)
    config["allow_abqjobpilot_real_enqueue"] = allow_real
    config["skip_real_jobpilot_enqueue"] = skip_real
    config["abqjobpilot"] = {"queue_only_confirmed": queue_only_confirmed, "project_root": str(tmp_path / "missing")}
    runner.config = config
    runner.workspace.config = config
    runner.workspace.save_config()
    auth = runner.run_step("05_jobpilot_enqueue_authorization")
    assert auth["verdict"] == "APPROVAL_REQUIRED"
    from abqpilot.core.approval import APPROVAL_PHRASE

    cli.command_approve_jobpilot_enqueue(runner.workspace.task_dir, "human", APPROVAL_PHRASE, 24)
    runner.run_step("05_jobpilot_enqueue_authorization")
    return runner


def _clear_abqjobpilot_modules():
    for name in list(sys.modules):
        if name == "abqjobpilot" or name.startswith("abqjobpilot."):
            del sys.modules[name]
