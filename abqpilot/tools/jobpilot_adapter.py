from __future__ import annotations

from pathlib import Path


class JobPilotAdapter:
    """Builds job request and command dictionaries without executing them."""

    def prepare(self, inp_path: str | Path, job_name: str = "abqpilot_mvp01", cpus: int = 14) -> dict:
        inp = Path(inp_path)
        command = f"abqjobpilot submit --input {inp} --job-name {job_name} --cpus {cpus} --dry-run"
        return {
            "adapter": "JobPilotAdapter",
            "mode": "dry_run",
            "inp_path": str(inp),
            "job_name": job_name,
            "cpus": cpus,
            "command": command,
            "dry_run": True,
            "executed": False,
        }
