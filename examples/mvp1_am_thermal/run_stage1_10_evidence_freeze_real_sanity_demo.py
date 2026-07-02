from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.analysis import build_evidence_package


RUN_DIR = PROJECT_ROOT / "runs" / "stage1_10_evidence_freeze_real_sanity_demo"
FINAL_PASS = "PASS_ABQPILOT_V2_STAGE1_10_REAL_SANITY_DEMO_EVIDENCE_FREEZE_READY"


def main() -> int:
    final = build_evidence_package(PROJECT_ROOT, RUN_DIR)
    print(f"verdict={final['verdict']}")
    print(f"output_dir={RUN_DIR}")
    print(f"manifest={final['evidence_manifest']}")
    print(f"summary={final['demo_trace_summary']}")
    print(f"report={final['report']}")
    print(f"artifact_index={final['artifact_index']}")
    return 0 if final["verdict"] == FINAL_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
