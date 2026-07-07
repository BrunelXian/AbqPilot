from pathlib import Path

from abqpilot.gui.controlled_solver_active_gate_writer_policy import evaluate_active_gate_writer_target


def test_writer_policy_imports_and_supports_fixture_mode(tmp_path: Path) -> None:
    result = evaluate_active_gate_writer_target(tmp_path, fixture_mode=True)
    assert result["policy_status"] == "ACTIVE_GATE_WRITER_TARGET_ALLOWED"
    assert result["fixture_write_supported"] is True
    assert result["real_task_write_enabled"] is False


def test_writer_policy_blocks_fixture_mode_false(tmp_path: Path) -> None:
    result = evaluate_active_gate_writer_target(tmp_path, fixture_mode=False)
    assert result["policy_status"] == "ACTIVE_GATE_WRITER_DISABLED_FOR_REAL_TASKS"


def test_writer_policy_blocks_real_task_gate_path() -> None:
    result = evaluate_active_gate_writer_target(
        r"D:\Projects\AbqPilot-v2\runs\tasks\example\gates",
        fixture_mode=True,
    )
    assert result["policy_status"] == "ACTIVE_GATE_WRITER_BLOCKED_REAL_TASK_GATE_PATH"


def test_writer_policy_blocks_forbidden_root() -> None:
    result = evaluate_active_gate_writer_target(
        r"D:\Users\wuxia\Documents\AbqPilot\tests\fixtures\gate",
        fixture_mode=True,
    )
    assert result["policy_status"] == "ACTIVE_GATE_WRITER_BLOCKED_FORBIDDEN_ROOT"


def test_writer_policy_blocks_runtime_and_source_paths() -> None:
    for path in (
        r"D:\Projects\AbqPilot-v2\runtime\queue",
        r"D:\Projects\AbqPilot-v2\tests\fixtures\source_sanity_base\gates",
    ):
        result = evaluate_active_gate_writer_target(path, fixture_mode=True)
        assert result["policy_status"] in {
            "ACTIVE_GATE_WRITER_BLOCKED_QUEUE_RUNTIME_STATUS_PATH",
            "ACTIVE_GATE_WRITER_BLOCKED_SOURCE_MODEL_PATH",
        }


def test_writer_policy_allows_only_stage5_2f_smoke_gate_path() -> None:
    allowed = evaluate_active_gate_writer_target(
        r"D:\Projects\AbqPilot-v2\runs\tasks\stage5_2f_controlled_solver_real_gate_smoke\gates",
        fixture_mode=False,
        stage5_2f_smoke_mode=True,
    )
    assert allowed["policy_status"] == "ACTIVE_GATE_WRITER_STAGE5_2F_SMOKE_TARGET_ALLOWED"
    blocked = evaluate_active_gate_writer_target(
        r"D:\Projects\AbqPilot-v2\runs\tasks\other_task\gates",
        fixture_mode=False,
        stage5_2f_smoke_mode=True,
    )
    assert blocked["policy_status"] == "ACTIVE_GATE_WRITER_BLOCKED_REAL_ARBITRARY_TASK"
