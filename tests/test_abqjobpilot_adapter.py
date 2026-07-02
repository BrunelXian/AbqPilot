import json
from types import SimpleNamespace
import sys

from abqpilot.integrations import AbqJobPilotPreflightAdapter, snapshot_runtime_files


def test_adapter_available_false_when_abqjobpilot_unavailable(monkeypatch):
    def missing(_name):
        raise ImportError("missing")

    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", missing)
    adapter = AbqJobPilotPreflightAdapter()
    assert adapter.available() is False


def test_adapter_build_request_is_preview_only(tmp_path):
    inp = tmp_path / "case.inp"
    inp.write_text("*Heading\n", encoding="utf-8")
    request = AbqJobPilotPreflightAdapter().build_request(
        inp_path=str(inp),
        job_name=None,
        cpus=14,
        batch="sanity",
        strategy="power_x2",
    )
    assert request["submission_mode"] == "preview_only"
    assert request["allow_solver_submit"] is False
    assert request["job_name"] == "case"


def test_adapter_preflight_calls_only_public_api_preflight(monkeypatch, tmp_path):
    calls = {"preflight": 0, "enqueue": 0}

    class FakeJobRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeClient:
        def preflight(self, request):
            calls["preflight"] += 1
            return {
                "status": "PREVIEW_READY",
                "job_id": request.kwargs["job_name"],
                "inp_exists": True,
                "expected_odb_path": "case.odb",
                "command_preview": "preview",
                "errors": [],
                "warnings": [],
            }

        def enqueue(self, *_args, **_kwargs):
            calls["enqueue"] += 1
            raise AssertionError("enqueue must not be called")

    monkeypatch.setattr(
        "abqpilot.integrations.abqjobpilot_adapter.importlib.import_module",
        lambda _name: SimpleNamespace(AbqJobPilotClient=FakeClient, JobRequest=FakeJobRequest),
    )
    inp = tmp_path / "case.inp"
    inp.write_text("*Heading\n", encoding="utf-8")
    adapter = AbqJobPilotPreflightAdapter()
    request = adapter.build_request(str(inp), "case", 14, "batch", "strategy")
    result = adapter.preflight(request)

    assert result["status"] == "PREVIEW_READY"
    assert calls == {"preflight": 1, "enqueue": 0}


def test_adapter_writes_preflight_artifacts(tmp_path):
    adapter = AbqJobPilotPreflightAdapter()
    request = adapter.build_request(str(tmp_path / "case.inp"), "case", 14, "batch", "strategy")
    result = {
        "status": "PREVIEW_READY",
        "job_id": "case",
        "inp_exists": False,
        "expected_odb_path": "case.odb",
        "command_preview": "python -m abqjobpilot.api.cli preflight --json",
        "errors": [],
        "warnings": [],
    }
    paths = adapter.write_preflight_artifacts(request, result, str(tmp_path / "out"))
    assert set(paths) == {
        "abqjobpilot_job_request",
        "abqjobpilot_preflight_result",
        "abqjobpilot_command_preview",
    }
    assert "No job was enqueued" in (tmp_path / "out" / "abqjobpilot_command_preview.md").read_text(encoding="utf-8")


def test_adapter_dry_run_enqueue_calls_public_api_with_dry_run_true(monkeypatch, tmp_path):
    calls = []

    class FakeJobRequest:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeClient:
        def enqueue(self, request, dry_run=False):
            calls.append((request.kwargs["job_name"], dry_run))
            if dry_run is not True:
                raise AssertionError("dry_run must be true")
            return {"status": "DRY_RUN_READY", "job_id": request.kwargs["job_name"], "errors": [], "warnings": []}

        def preflight(self, *_args, **_kwargs):
            raise AssertionError("preflight must not be called by dry_run_enqueue")

    monkeypatch.setattr(
        "abqpilot.integrations.abqjobpilot_adapter.importlib.import_module",
        lambda _name: SimpleNamespace(AbqJobPilotClient=FakeClient, JobRequest=FakeJobRequest),
    )
    adapter = AbqJobPilotPreflightAdapter()
    request = _request(tmp_path)

    result = adapter.dry_run_enqueue(request)

    assert result["status"] == "DRY_RUN_READY"
    assert result["runtime_mutation_detected"] is False
    assert calls == [("case", True)]


def test_adapter_dry_run_rejects_allow_solver_submit_before_api_call(monkeypatch, tmp_path):
    calls = []

    def forbidden_import(_name):
        calls.append("imported")
        raise AssertionError("unsafe request should be rejected before import")

    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", forbidden_import)
    request = _request(tmp_path)
    request["allow_solver_submit"] = True

    result = AbqJobPilotPreflightAdapter().dry_run_enqueue(request)

    assert result["status"] == "UNSAFE_JOBPILOT_REQUEST_REJECTED"
    assert calls == []


def test_adapter_dry_run_rejects_submit_mode_before_api_call(monkeypatch, tmp_path):
    calls = []

    def forbidden_import(_name):
        calls.append("imported")
        raise AssertionError("unsafe request should be rejected before import")

    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", forbidden_import)
    request = _request(tmp_path)
    request["submission_mode"] = "submit"

    result = AbqJobPilotPreflightAdapter().dry_run_enqueue(request)

    assert result["status"] == "UNSAFE_JOBPILOT_REQUEST_REJECTED"
    assert calls == []


def test_snapshot_runtime_files_detects_queue_mutation(tmp_path):
    root = tmp_path / "abqjobpilot_dev"
    runtime = root / "runtime"
    runtime.mkdir(parents=True)
    queue = runtime / "queue.json"
    queue.write_text("[]", encoding="utf-8")

    before = snapshot_runtime_files(str(root))
    queue.write_text("[{}]", encoding="utf-8")
    after = snapshot_runtime_files(str(root))

    assert before != after


def test_snapshot_runtime_files_passes_when_runtime_unchanged(tmp_path):
    root = tmp_path / "abqjobpilot_dev"
    runtime = root / "runtime"
    reports = runtime / "reports"
    reports.mkdir(parents=True)
    (runtime / "queue.json").write_text("[]", encoding="utf-8")
    (runtime / "live_status.json").write_text("{}", encoding="utf-8")

    before = snapshot_runtime_files(str(root))
    after = snapshot_runtime_files(str(root))

    assert before == after


def test_adapter_writes_dry_run_enqueue_artifacts(tmp_path):
    adapter = AbqJobPilotPreflightAdapter(project_root=str(tmp_path))
    request = adapter.build_request(str(tmp_path / "case.inp"), "case", 14, "batch", "strategy")
    result = {
        "status": "DRY_RUN_READY",
        "dry_run": True,
        "runtime_mutation_detected": False,
        "runtime_snapshot_before": snapshot_runtime_files(str(tmp_path)),
        "runtime_snapshot_after": snapshot_runtime_files(str(tmp_path)),
        "errors": [],
        "warnings": [],
    }

    paths = adapter.write_dry_run_enqueue_artifacts(request, result, str(tmp_path / "out"))

    assert set(paths) == {
        "abqjobpilot_dry_run_request",
        "abqjobpilot_dry_run_enqueue_result",
        "abqjobpilot_dry_run_safety_report",
        "abqjobpilot_dry_run_preview",
    }
    saved = json.loads((tmp_path / "out" / "abqjobpilot_dry_run_enqueue_result.json").read_text(encoding="utf-8"))
    assert saved["status"] == "DRY_RUN_READY"
    assert "No job was enqueued" in (tmp_path / "out" / "abqjobpilot_dry_run_preview.md").read_text(encoding="utf-8")


def test_adapter_missing_project_root_returns_unavailable(tmp_path):
    adapter = AbqJobPilotPreflightAdapter(project_root=str(tmp_path / "missing"))
    result = adapter.preflight(_request(tmp_path))

    assert result["status"] == "ABQJOBPILOT_UNAVAILABLE"
    diagnostics = adapter.diagnostics()
    assert diagnostics["available"] is False
    assert diagnostics["api_path_exists"] is False


def test_adapter_project_root_missing_api_returns_unavailable(tmp_path):
    root = tmp_path / "abqjobpilot_dev"
    root.mkdir()
    adapter = AbqJobPilotPreflightAdapter(project_root=str(root))
    result = adapter.preflight(_request(tmp_path))

    assert result["status"] == "ABQJOBPILOT_UNAVAILABLE"
    assert adapter.diagnostics()["api_path_exists"] is False


def test_adapter_adds_valid_project_root_to_syspath_and_imports_api(tmp_path, monkeypatch):
    _clear_abqjobpilot_modules()
    root = _write_fake_api(tmp_path)
    root_text = str(root)
    if root_text in sys.path:
        sys.path.remove(root_text)

    adapter = AbqJobPilotPreflightAdapter(project_root=root_text)

    assert adapter.available() is True
    assert root_text in sys.path
    assert adapter.diagnostics()["api_path_exists"] is True


def test_adapter_imports_only_public_api_not_gui(tmp_path, monkeypatch):
    _clear_abqjobpilot_modules()
    imported = []
    root = _write_fake_api(tmp_path)
    import importlib
    real_import_module = importlib.import_module

    def tracking_import_module(name, *args, **kwargs):
        imported.append(name)
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr("abqpilot.integrations.abqjobpilot_adapter.importlib.import_module", tracking_import_module)
    adapter = AbqJobPilotPreflightAdapter(project_root=str(root))
    assert adapter.available() is True
    assert any(name.startswith("abqjobpilot.api") for name in imported)
    assert not any("gui" in name.lower() for name in imported)


def _request(tmp_path):
    inp = tmp_path / "case.inp"
    inp.write_text("*Heading\n", encoding="utf-8")
    return AbqJobPilotPreflightAdapter().build_request(str(inp), "case", 14, "batch", "strategy")


def _write_fake_api(tmp_path):
    root = tmp_path / "fake_abqjobpilot"
    api = root / "abqjobpilot" / "api"
    api.mkdir(parents=True)
    (root / "abqjobpilot" / "__init__.py").write_text("", encoding="utf-8")
    (api / "__init__.py").write_text(
        """
class JobRequest:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

class AbqJobPilotClient:
    def preflight(self, request):
        return {
            "status": "PREVIEW_READY",
            "job_id": request.kwargs.get("job_name"),
            "inp_exists": True,
            "expected_odb_path": "case.odb",
            "command_preview": "preview",
            "errors": [],
            "warnings": [],
        }

    def enqueue(self, *args, **kwargs):
        raise AssertionError("enqueue must not be called")
""",
        encoding="utf-8",
    )
    return root


def _clear_abqjobpilot_modules():
    for name in list(sys.modules):
        if name == "abqjobpilot" or name.startswith("abqjobpilot."):
            del sys.modules[name]
