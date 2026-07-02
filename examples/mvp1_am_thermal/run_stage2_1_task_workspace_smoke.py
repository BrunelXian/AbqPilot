from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.core.pipeline_runner import PipelineRunner


def main() -> int:
    runner = PipelineRunner(
        config_path=PROJECT_ROOT / "configs" / "sanity_demo_task.json",
        task_id="stage2_1_workspace_smoke",
    )
    result = runner.run_until("07_solver_intake")
    state = json.loads(runner.workspace.state_path.read_text(encoding="utf-8"))
    artifacts = json.loads(runner.workspace.artifacts_path.read_text(encoding="utf-8"))

    print(f"task_dir={runner.workspace.task_dir}")
    print(f"verdict={result['verdict']}")
    print(f"task_state={json.dumps(state, ensure_ascii=False)}")
    print(f"artifact_registry={json.dumps(artifacts, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
