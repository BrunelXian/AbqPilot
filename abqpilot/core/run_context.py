from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    project_root: Path
    run_dir: Path
    base_inp_path: Path
    objective_spec_path: Path
    metrics_path: Path | None = None

    @property
    def generated_inp_path(self) -> Path:
        return self.run_dir / "generated.inp"

    @property
    def build_request_path(self) -> Path:
        return self.run_dir / "build_request.json"

