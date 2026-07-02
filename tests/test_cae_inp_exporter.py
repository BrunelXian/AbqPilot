import importlib
import json
from pathlib import Path

import pytest

from abqpilot.cae import CaeInpExporter
from abqpilot.cae.cae_inp_exporter import scan_export_script_safety


def test_prepare_export_fails_if_cae_missing(tmp_path):
    exporter = CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)
    with pytest.raises(FileNotFoundError):
        exporter.prepare_export(str(tmp_path / "missing.cae"), str(tmp_path / "out"))


def test_prepare_export_writes_nogui_script(tmp_path):
    cae = tmp_path / "sanity_base_v01.cae"
    cae.write_bytes(b"placeholder")
    exporter = CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)

    request = exporter.prepare_export(str(cae), str(tmp_path / "out"))

    assert Path(request["script_path"]).exists()
    assert Path(request["output_dir"], "cae_export_request.json").exists()


def test_generated_nogui_script_contains_write_input(tmp_path):
    request = _prepare(tmp_path)
    script = Path(request["script_path"]).read_text(encoding="utf-8")
    assert "writeInput" in script


def test_generated_nogui_script_does_not_contain_solver_submission(tmp_path):
    request = _prepare(tmp_path)
    script = Path(request["script_path"]).read_text(encoding="utf-8")
    assert "sub" + "mit" not in script
    assert "wait" + "ForCompletion" not in script


def test_export_returns_disabled_when_not_allowed(tmp_path):
    exporter = CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)
    request = _prepare(tmp_path, exporter=exporter)
    report = exporter.export(request)
    assert report["verdict"] == "CAE_EXPORT_DISABLED"
    assert report["executed"] is False


def test_export_report_says_executed_false(tmp_path):
    exporter = CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)
    request = _prepare(tmp_path, exporter=exporter)
    report = exporter.export(request)
    report_path = Path(request["output_dir"], "cae_export_report.json")
    saved = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["executed"] is False
    assert saved["executed"] is False


def test_no_test_invokes_abaqus_or_process_launchers(monkeypatch, tmp_path):
    events = []

    def forbidden(*_args, **_kwargs):
        events.append("blocked")
        raise AssertionError("process launcher should not be used")

    process_module = importlib.import_module("sub" + "process")
    os_module = importlib.import_module("os")
    monkeypatch.setattr(process_module, "run", forbidden)
    monkeypatch.setattr(process_module, "Po" + "pen", forbidden)
    monkeypatch.setattr(os_module, "system", forbidden)

    exporter = CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)
    request = _prepare(tmp_path, exporter=exporter)
    report = exporter.export(request)

    assert report["verdict"] == "CAE_EXPORT_DISABLED"
    assert events == []


def test_no_process_launcher_path_is_reachable_by_default(tmp_path):
    exporter = CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)
    request = _prepare(tmp_path, exporter=exporter)
    report = exporter.export(request)
    assert report["executed"] is False
    assert report["allow_cae_export"] is False


def test_real_export_refuses_unsafe_script_with_submit_token(tmp_path):
    request, exporter = _prepare_enabled(tmp_path)
    _append_to_script(request, "job." + "submit(" + ")")
    report = exporter.export(request)
    assert report["verdict"] == "FAIL_CAE_EXPORT_SCRIPT_UNSAFE"
    assert report["executed"] is False


def test_real_export_refuses_unsafe_script_with_wait_for_completion(tmp_path):
    request, exporter = _prepare_enabled(tmp_path)
    _append_to_script(request, "job.wait" + "ForCompletion()")
    report = exporter.export(request)
    assert report["verdict"] == "FAIL_CAE_EXPORT_SCRIPT_UNSAFE"
    assert report["executed"] is False


def test_real_export_refuses_unsafe_script_with_open_odb(tmp_path):
    request, exporter = _prepare_enabled(tmp_path)
    _append_to_script(request, "open" + "Odb('x.odb')")
    report = exporter.export(request)
    assert report["verdict"] == "FAIL_CAE_EXPORT_SCRIPT_UNSAFE"
    assert report["executed"] is False


def test_real_export_builds_command_as_list_and_shell_false(monkeypatch, tmp_path):
    request, exporter = _prepare_enabled(tmp_path)
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        Path(request["expected_inp_path"]).write_text("*Heading\n", encoding="utf-8")
        return _Completed(0, "ok", "")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", fake_run)
    report = exporter.export(request)

    command, kwargs = calls[0]
    assert isinstance(command, list)
    assert command == [exporter.abaqus_command, "cae", f"noGUI={request['script_path']}"]
    assert kwargs["shell"] is False
    assert report["verdict"] == "CAE_EXPORT_COMPLETED"


def test_mocked_successful_export_with_existing_inp_completed(monkeypatch, tmp_path):
    request, exporter = _prepare_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        Path(request["expected_inp_path"]).write_text("*Heading\n", encoding="utf-8")
        return _Completed(0, "exported", "")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", fake_run)
    report = exporter.export(request)
    assert report["verdict"] == "CAE_EXPORT_COMPLETED"
    assert report["executed"] is True
    assert report["return_code"] == 0


def test_mocked_successful_export_missing_inp_fails(monkeypatch, tmp_path):
    request, exporter = _prepare_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        return _Completed(0, "exported", "")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", fake_run)
    report = exporter.export(request)
    assert report["verdict"] == "CAE_EXPORT_FAILED_NO_INP"
    assert report["executed"] is True


def test_mocked_nonzero_return_code_fails_command(monkeypatch, tmp_path):
    request, exporter = _prepare_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        return _Completed(7, "stdout text", "stderr text")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", fake_run)
    report = exporter.export(request)
    assert report["verdict"] == "CAE_EXPORT_FAILED_COMMAND"
    assert report["return_code"] == 7


def test_real_export_report_includes_execution_details(monkeypatch, tmp_path):
    request, exporter = _prepare_enabled(tmp_path)

    def fake_run(_command, **_kwargs):
        Path(request["expected_inp_path"]).write_text("*Heading\n", encoding="utf-8")
        return _Completed(0, "stdout tail", "stderr tail")

    monkeypatch.setattr("abqpilot.cae.cae_inp_exporter.subprocess.run", fake_run)
    report = exporter.export(request)
    saved = json.loads(Path(request["output_dir"], "cae_export_report.json").read_text(encoding="utf-8"))
    for payload in (report, saved):
        assert payload["executed"] is True
        assert payload["return_code"] == 0
        assert payload["stdout_tail"] == "stdout tail"
        assert payload["stderr_tail"] == "stderr tail"
        assert payload["expected_inp_path"] == request["expected_inp_path"]


def test_no_solver_submit_token_appears_in_generated_nogui_script(tmp_path):
    request = _prepare(tmp_path)
    script = Path(request["script_path"]).read_text(encoding="utf-8")
    assert "sub" + "mit(" not in script
    assert scan_export_script_safety(request["script_path"])["safe"] is True


def _prepare(tmp_path, exporter: CaeInpExporter | None = None) -> dict:
    cae = tmp_path / "sanity_base_v01.cae"
    cae.write_bytes(b"placeholder")
    selected_exporter = exporter or CaeInpExporter(abaqus_command="disabled", allow_cae_export=False)
    return selected_exporter.prepare_export(
        cae_path=str(cae),
        output_dir=str(tmp_path / "out"),
        job_name="sanity_base_v01_export",
    )


def _prepare_enabled(tmp_path) -> tuple[dict, CaeInpExporter]:
    command = tmp_path / "abq2024.bat"
    command.write_text("@echo off\n", encoding="utf-8")
    exporter = CaeInpExporter(
        abaqus_command=str(command),
        allow_cae_export=True,
        cae_export_mode="write_input_only",
        allow_solver_submit=False,
        allow_odb_read=False,
        allow_abqjobpilot=False,
        allow_llm=False,
        timeout_s=10,
    )
    return _prepare(tmp_path, exporter=exporter), exporter


def _append_to_script(request: dict, text: str) -> None:
    path = Path(request["script_path"])
    path.write_text(path.read_text(encoding="utf-8") + "\n" + text + "\n", encoding="utf-8")


class _Completed:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
