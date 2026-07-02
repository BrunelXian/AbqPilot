from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from abqpilot.core.pipeline_runner import PipelineRunner


def main() -> int:
    config_path = PROJECT_ROOT / "configs" / "sanity_demo_task.json"
    task_id = "stage2_2_resume_skip_rerun_smoke"

    runner = PipelineRunner(config_path=config_path, task_id=task_id)
    prepare = runner.run_until("07_solver_intake", mode_limit=True)

    resumed = PipelineRunner.open_existing(config_path=config_path, task_id=task_id)
    resume_result = resumed.resume()

    skipped = resumed.run_step("01_export_cae")
    forced = None
    exported = resumed.workspace.registry.get_artifact("exported_inp")
    if exported and Path(exported["path"]).exists():
        forced = resumed.run_step("02_audit_heat_x2", force=True)
        if forced["success"]:
            resumed.workspace.stop_by_mode_limit()

    state = json.loads(resumed.workspace.state_path.read_text(encoding="utf-8"))
    trace = json.loads(resumed.workspace.trace_path.read_text(encoding="utf-8"))["events"]

    print(f"task_dir={resumed.workspace.task_dir}")
    print(f"prepare_verdict={prepare['verdict']}")
    print(f"resume_verdict={resume_result['verdict']}")
    print(f"skip_verdict={skipped['verdict']}")
    print(f"force_verdict={forced['verdict'] if forced else 'SKIPPED_NO_EXPORTED_INP'}")
    print(f"task_state={json.dumps(state, ensure_ascii=False)}")
    print(f"trace_events={len(trace)}")
    for event in trace[-8:]:
        print(f"trace={event['event']} step={event['step']} verdict={event['verdict']} reason={event['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
