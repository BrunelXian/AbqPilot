from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.cli import (
    command_audit_heat_x2,
    command_compare_metrics,
    command_intake_solver,
    command_status,
)


def main() -> int:
    run_dir = PROJECT_ROOT / "runs" / "stage2_0_cli_smoke"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("## status")
    status = command_status()
    print(f"verdict={status['verdict']}")

    print("## compare-metrics")
    metrics_path = PROJECT_ROOT / "runs" / "stage1_8_gated_odb_metrics_extraction" / "odb_metrics_pair.json"
    compare = command_compare_metrics(metrics_path, run_dir / "compare")
    print(f"verdict={compare['verdict']}")
    print(f"NT_max_ratio={compare['details']['key_ratios'].get('NT_max')}")
    print(f"S_Mises_max_ratio={compare['details']['key_ratios'].get('S_Mises_max')}")

    print("## audit-heat-x2")
    source_inp = PROJECT_ROOT / "runs" / "stage1_6a_cae_to_inp_export" / "sanity_base_v01_export.inp"
    if source_inp.exists():
        audit = command_audit_heat_x2(source_inp, run_dir / "audit_heat_x2", 2.0)
        print(f"verdict={audit['verdict']}")
        print(f"original_magnitude={audit['details'].get('original_magnitude')}")
        print(f"modified_magnitude={audit['details'].get('modified_magnitude')}")
    else:
        print("verdict=SKIP_SOURCE_INP_MISSING")

    print("## intake-solver")
    solver_root = PROJECT_ROOT / "CAE_model" / "sanity_base"
    if solver_root.exists():
        intake = command_intake_solver(solver_root, run_dir / "solver_intake")
        print(f"verdict={intake['verdict']}")
        print(f"cases_detected={intake['details'].get('cases_detected')}")
    else:
        print("verdict=SKIP_SOLVER_ROOT_MISSING")

    print(f"run_dir={run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
