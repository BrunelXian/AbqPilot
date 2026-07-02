from __future__ import annotations

from abqpilot.execution.base import JobExecutionBackend


class AbqJobPilotBackend(JobExecutionBackend):
    """Stub for future abqjobpilot integration.

    Real integration is intentionally disabled until explicitly approved. This
    class must not import, call, submit to, or otherwise execute the user's
    existing abqjobpilot project.
    """

    def __init__(
        self,
        abqjobpilot_root: str | None = None,
        python_executable: str | None = None,
        allow_real_execution: bool = False,
    ) -> None:
        self.abqjobpilot_root = abqjobpilot_root
        self.python_executable = python_executable
        self.allow_real_execution = allow_real_execution

    def submit(self, job_request: dict) -> dict:
        raise NotImplementedError("Real abqjobpilot execution is disabled for Stage 1.5")

    def status(self, job_id: str) -> dict:
        raise NotImplementedError("Real abqjobpilot status polling is disabled for Stage 1.5")

