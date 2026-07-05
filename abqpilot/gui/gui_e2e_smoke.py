from __future__ import annotations

from pathlib import Path
from typing import Any

from abqpilot.gui.beta_smoke import build_gui_beta_e2e_smoke, write_gui_beta_e2e_smoke_outputs


def build_gui_e2e_smoke_view(project_root: str | Path, task_dir: str | Path | None = None) -> dict[str, Any]:
    return build_gui_beta_e2e_smoke(project_root, task_dir=task_dir)


def write_gui_e2e_smoke_report(project_root: str | Path, task_dir: str | Path | None = None) -> dict[str, Any]:
    return write_gui_beta_e2e_smoke_outputs(project_root, task_dir=task_dir)
