from abqpilot.tools.physics_guard_tool import PhysicsGuard


def test_physics_guard_fails_on_forbidden_diff_guard_report():
    report = PhysicsGuard().check({"allowed": False, "forbidden_changed": True, "uncertainty": False})
    assert report["passed"] is False


def test_physics_guard_fails_on_uncertain_diff_guard_report():
    report = PhysicsGuard().check({"allowed": False, "forbidden_changed": False, "uncertainty": True})
    assert report["passed"] is False

