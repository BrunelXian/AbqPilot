from abqpilot.workspace_guard import (
    FORBIDDEN_ROOT,
    PROJECT_ROOT,
    is_forbidden_root,
    is_project_root,
    verify_cleanup_target,
    verify_write_target,
)


def test_workspace_guard_imports_and_recognizes_roots() -> None:
    assert is_project_root(PROJECT_ROOT)
    assert is_forbidden_root(FORBIDDEN_ROOT / "tests" / "test_controlled_solver_demo_smoke.py")


def test_workspace_guard_allows_project_write_and_blocks_forbidden_write() -> None:
    allowed = verify_write_target(PROJECT_ROOT / "docs" / "WORKSPACE_ROOT_GUARD.md")
    blocked = verify_write_target(FORBIDDEN_ROOT / "tests" / "test_controlled_solver_demo_smoke.py")
    assert allowed.allowed is True
    assert allowed.reason == "PROJECT_ROOT_WRITE_ALLOWED"
    assert blocked.allowed is False
    assert blocked.reason == "FORBIDDEN_ROOT"


def test_workspace_guard_cleanup_target_classification() -> None:
    approved = verify_cleanup_target(FORBIDDEN_ROOT / "tests" / "test_controlled_solver_demo_smoke.py")
    unrelated = verify_cleanup_target(FORBIDDEN_ROOT / "notes" / "keep_me.py")
    assert approved.allowed is True
    assert approved.reason == "APPROVED_STAGE5_3A_CLEANUP_TARGET"
    assert unrelated.allowed is False
    assert unrelated.reason == "FORBIDDEN_ROOT_CLEANUP_NOT_APPROVED"
