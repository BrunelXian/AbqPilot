from __future__ import annotations

from pathlib import Path

from abqpilot.pipeline_protocol.task_scaffold import GATES, HANDOFFS, RUNS, scaffold_pipeline_task


def test_task_scaffold_creates_flat_trace_and_required_dirs(tmp_path) -> None:
    result = scaffold_pipeline_task("demo_pipeline_task", root=tmp_path)
    task_dir = Path(result["task_dir"])
    assert (task_dir / "TASK_PLAN.md").exists()
    assert (task_dir / "TRACE_INDEX.md").exists()
    assert (task_dir / "TASK_FINAL_EVIDENCE_LEDGER.md").exists()
    assert (task_dir / "handoffs").is_dir()
    assert (task_dir / "gates").is_dir()
    for run_id, name, *_ in RUNS:
        trace_file = task_dir / "trace" / f"{run_id}_{name}.md"
        assert trace_file.exists()
        assert trace_file.is_file()
        assert not (task_dir / "trace" / run_id).exists()
        assert (task_dir / "artifacts" / f"{run_id.lower()}_{name.lower()}").is_dir()
    for handoff_id, name, *_ in HANDOFFS:
        assert (task_dir / "handoffs" / f"{handoff_id}_{name}.md").exists()
    for gate_id, name, *_ in GATES:
        assert (task_dir / "gates" / f"{gate_id}_{name}.md").exists()
