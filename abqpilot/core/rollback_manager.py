from __future__ import annotations

from pathlib import Path


class RollbackManager:
    """Placeholder for future controlled rollback support."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.snapshots: list[dict] = []

    def record(self, label: str, path: Path) -> dict:
        snapshot = {"label": label, "path": str(path), "mode": "placeholder"}
        self.snapshots.append(snapshot)
        return snapshot

