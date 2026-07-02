from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactRegistry:
    def __init__(self, task_id: str, artifacts: list[dict[str, Any]] | None = None) -> None:
        self.task_id = task_id
        self.artifacts = artifacts or []

    def add_artifact(
        self,
        name: str,
        kind: str,
        path: str | Path,
        producer_step: str | None = None,
    ) -> dict[str, Any]:
        artifact = {
            "name": name,
            "kind": kind,
            "path": str(path),
            "exists": Path(path).exists(),
            "producer_step": producer_step,
        }
        existing = self.get_artifact(name)
        if existing is None:
            self.artifacts.append(artifact)
        else:
            existing.update(artifact)
            artifact = existing
        return artifact

    def get_artifact(self, name: str) -> dict[str, Any] | None:
        return next((artifact for artifact in self.artifacts if artifact.get("name") == name), None)

    def to_dict(self) -> dict[str, Any]:
        for artifact in self.artifacts:
            artifact["exists"] = Path(artifact["path"]).exists()
        return {"task_id": self.task_id, "artifacts": self.artifacts}

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ArtifactRegistry":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(task_id=payload["task_id"], artifacts=payload.get("artifacts", []))
