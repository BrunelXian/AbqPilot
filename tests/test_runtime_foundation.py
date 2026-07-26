from pathlib import Path

import pytest

from abqpilot.runtime.context import AbqPilotContext
from abqpilot.runtime.controlled_workspace import ControlledWorkspace, WorkspaceViolation
from abqpilot.runtime.executor import ControlledExecutor, ExecutionRequest


def _context(tmp_path: Path) -> AbqPilotContext:
    project = tmp_path / "project"
    source = project / "source"
    staging = project / "staging"
    output = project / "output"
    evidence = project / "evidence"
    for path in (source, staging, output, evidence):
        path.mkdir(parents=True, exist_ok=True)
    return AbqPilotContext(
        schema_version="1.0",
        session_id="session-1",
        run_id="run-1",
        task_id="task-1",
        project_root=project,
        source_root=source,
        staging_root=staging,
        output_root=output,
        evidence_root=evidence,
        abaqus_command="abq.bat",
        expected_abaqus_version="2024",
        cpu_limit=14,
        execution_mode="DRY_RUN",
        policy_id="test-policy",
        allowed_tools=("submit_solver",),
    )


def test_context_round_trip(tmp_path: Path) -> None:
    context = _context(tmp_path)
    path = tmp_path / "context.json"

    context.save(path)
    restored = AbqPilotContext.load(path)

    assert restored == context
    assert restored.allowed_tools == ("submit_solver",)


def test_workspace_blocks_source_write_and_escape(tmp_path: Path) -> None:
    context = _context(tmp_path)
    workspace = ControlledWorkspace(context)

    allowed = workspace.resolve_write(context.staging_root / "candidate.inp", scope="staging")
    assert allowed.path == context.staging_root / "candidate.inp"

    with pytest.raises(WorkspaceViolation, match="not writable"):
        workspace.resolve_write(context.source_root / "base.inp", scope="source")

    with pytest.raises(WorkspaceViolation, match="WRITE_OUTSIDE_OUTPUT_ROOT"):
        workspace.resolve_write(tmp_path / "outside.odb", scope="output")

    with pytest.raises(WorkspaceViolation, match="EXECUTION_CWD_OUTSIDE_RUNTIME_ROOTS"):
        workspace.resolve_execution_cwd(context.source_root)


def test_executor_enforces_context_and_uses_shell_false(tmp_path: Path) -> None:
    context = _context(tmp_path)
    calls = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, cwd, capture_output, text, timeout, shell):
        calls.update(
            command=command,
            cwd=cwd,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            shell=shell,
        )
        return Completed()

    executor = ControlledExecutor(context, process_runner=fake_run)
    result = executor.execute(
        ExecutionRequest(
            tool_name="submit_solver",
            command=("abq.bat", "job=test", "interactive"),
            cwd=context.output_root,
            timeout_s=10,
            authorization_id="approval-1",
        )
    )

    assert result.return_code == 0
    assert result.process_started is True
    assert calls["shell"] is False
    assert calls["cwd"] == context.output_root


def test_executor_rejects_unknown_tool_and_wrong_executable(tmp_path: Path) -> None:
    context = _context(tmp_path)
    executor = ControlledExecutor(context, process_runner=lambda *args, **kwargs: None)

    with pytest.raises(PermissionError, match="tool is not allowed"):
        executor.execute(
            ExecutionRequest(
                tool_name="arbitrary_shell",
                command=("abq.bat", "job=test"),
                cwd=context.output_root,
                timeout_s=10,
                authorization_id="approval-1",
            )
        )

    with pytest.raises(PermissionError, match="executable does not match"):
        executor.execute(
            ExecutionRequest(
                tool_name="submit_solver",
                command=("python", "unsafe.py"),
                cwd=context.output_root,
                timeout_s=10,
                authorization_id="approval-1",
            )
        )
