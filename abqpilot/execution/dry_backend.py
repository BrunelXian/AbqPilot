from __future__ import annotations

from abqpilot.execution.base import JobExecutionBackend


class DryRunBackend(JobExecutionBackend):
    """Deterministic execution backend that simulates submission only."""

    def __init__(self) -> None:
        self._counter = 0
        self.submissions: list[dict] = []

    def submit(self, job_request: dict) -> dict:
        self._counter += 1
        job_id = f"dry_{self._counter:04d}"
        submission = {
            "backend": "dry",
            "dry_run": True,
            "job_id": job_id,
            "status": "DRY_SUBMITTED",
            "command": job_request.get("command"),
            "executed": False,
        }
        self.submissions.append({"job_request": dict(job_request), "job_submission": dict(submission)})
        return submission

    def status(self, job_id: str) -> dict:
        return {
            "backend": "dry",
            "dry_run": True,
            "job_id": job_id,
            "status": "DRY_COMPLETED",
            "executed": False,
        }

