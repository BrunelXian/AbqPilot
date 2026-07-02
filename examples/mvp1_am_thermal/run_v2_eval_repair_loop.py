from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.tools.eval_repair_tool import EvalRepairTool


def main() -> int:
    example_dir = Path(__file__).resolve().parent
    objective = _read_json(example_dir / "objective_spec.json")
    history = _read_json(example_dir / "parameter_history_empty.json")
    tool = EvalRepairTool()

    for name in ["low", "pass", "high"]:
        metrics = _read_json(example_dir / f"odb_metrics_{name}.json")
        evaluation, repair_plan = tool.evaluate(objective, metrics, history)
        print(
            f"{name}: result={evaluation['result']} "
            f"final_state={evaluation['final_state']} "
            f"action={repair_plan['action']} "
            f"next_scale={repair_plan['next_heat_flux_scale']}"
        )
    return 0


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    raise SystemExit(main())

