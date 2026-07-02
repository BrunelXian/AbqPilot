from __future__ import annotations

from abqpilot.execution.abqjobpilot_backend import AbqJobPilotBackend
from abqpilot.execution.base import JobExecutionBackend
from abqpilot.execution.dry_backend import DryRunBackend


def create_execution_backend(config: dict) -> JobExecutionBackend:
    runtime_config = config.get("runtime", config)
    backend_name = runtime_config.get("execution_backend")
    allow_real_execution = bool(runtime_config.get("allow_real_execution", False))

    if backend_name is None:
        raise ValueError("execution_backend is required")

    normalized = str(backend_name).strip().lower()
    if normalized == "dry":
        return DryRunBackend()
    if normalized == "abqjobpilot":
        backend = AbqJobPilotBackend(
            abqjobpilot_root=runtime_config.get("abqjobpilot_root"),
            python_executable=runtime_config.get("python_executable"),
            allow_real_execution=allow_real_execution,
        )
        raise NotImplementedError(
            "abqjobpilot backend is intentionally disabled until explicitly approved"
        )
    raise ValueError(f"Unsupported execution_backend: {backend_name}")

