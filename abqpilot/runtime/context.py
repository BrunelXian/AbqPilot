from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AbqPilotContext:
    """Versioned, serializable runtime authority for one controlled run.

    The context contains resolved runtime identity, filesystem roots, execution
    policy and resource limits.  It deliberately contains no live objects so it
    can be persisted into the evidence trail and reconstructed after restart.
    """

    schema_version: str
    session_id: str
    run_id: str
    task_id: str

    project_root: Path
    source_root: Path
    staging_root: Path
    output_root: Path
    evidence_root: Path

    abaqus_command: str
    expected_abaqus_version: str | None
    cpu_limit: int

    execution_mode: str
    policy_id: str
    allowed_tools: tuple[str, ...]
    active_plan_id: str | None = None

    def __post_init__(self) -> None:
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")
        for name in ("session_id", "run_id", "task_id", "execution_mode", "policy_id"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must not be empty")
        if self.cpu_limit < 1:
            raise ValueError("cpu_limit must be at least 1")

        for name in ("project_root", "source_root", "staging_root", "output_root", "evidence_root"):
            object.__setattr__(self, name, Path(getattr(self, name)).expanduser().resolve(strict=False))

        object.__setattr__(self, "allowed_tools", tuple(dict.fromkeys(self.allowed_tools)))

    @classmethod
    def for_existing_solver_run(
        cls,
        run_dir: str | Path,
        *,
        abaqus_command: str,
        cpu_limit: int,
        run_id: str | None = None,
    ) -> "AbqPilotContext":
        """Compatibility context for an existing single-directory solver run.

        This adapter allows legacy solver corridors to enter the new runtime
        boundary before their source/staging/output roots are physically split.
        New workflows should construct explicit, non-overlapping roots instead.
        """

        root = Path(run_dir).expanduser().resolve(strict=False)
        identity = run_id or root.name
        return cls(
            schema_version="1.0",
            session_id=f"legacy-session:{identity}",
            run_id=identity,
            task_id=identity,
            project_root=root,
            source_root=root,
            staging_root=root,
            output_root=root,
            evidence_root=root,
            abaqus_command=abaqus_command,
            expected_abaqus_version=None,
            cpu_limit=cpu_limit,
            execution_mode="LEGACY_SOLVER_CORRIDOR",
            policy_id="runtime-foundation-v01",
            allowed_tools=("submit_solver",),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for name in ("project_root", "source_root", "staging_root", "output_root", "evidence_root"):
            payload[name] = str(payload[name])
        payload["allowed_tools"] = list(self.allowed_tools)
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AbqPilotContext":
        known = {field.name for field in fields(cls)}
        unknown = set(payload) - known
        if unknown:
            raise ValueError(f"unknown context fields: {sorted(unknown)}")
        values = dict(payload)
        values["allowed_tools"] = tuple(values.get("allowed_tools", ()))
        return cls(**values)

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "AbqPilotContext":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("context payload must be a JSON object")
        return cls.from_dict(payload)
