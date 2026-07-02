from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.core.orchestrator import DeterministicOrchestrator
from abqpilot.core.run_context import RunContext


def main() -> int:
    example_dir = Path(__file__).resolve().parent
    run_dir = PROJECT_ROOT / "runs" / "mvp1_am_thermal_dry_pipeline"
    context = RunContext(
        project_root=PROJECT_ROOT,
        run_dir=run_dir,
        base_inp_path=example_dir / "base_heatflux_marker.inp",
        objective_spec_path=example_dir / "objective_spec.json",
        metrics_path=example_dir / "odb_metrics_pass.json",
    )
    result = DeterministicOrchestrator(context).run()
    print(f"final_state={result['final_state']}")
    print(f"verdict={result['verdict']}")
    print(f"trace_json={result['trace']['trace_json']}")
    return 0 if result["final_state"] in {"PASS", "REPAIR", "JOB_REQUEST_READY"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

