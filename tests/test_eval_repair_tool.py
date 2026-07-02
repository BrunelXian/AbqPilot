from abqpilot.tools.eval_repair_tool import EvalRepairTool


OBJECTIVE = {
    "target_range": [480.0, 520.0],
    "initial_parameters": {"heat_flux_scale": 1.0},
    "stop_rules": {"max_iterations": 3},
}


def test_eval_repair_tool_returns_pass_for_in_range_temperature():
    evaluation, repair = EvalRepairTool().evaluate(
        OBJECTIVE, {"observed_mean": 500.0}, {"iterations": []}
    )
    assert evaluation["result"] == "PASS"
    assert evaluation["final_state"] == "PASS"
    assert repair["allowed"] is False


def test_eval_repair_tool_returns_fail_low_and_scale_increase():
    evaluation, repair = EvalRepairTool().evaluate(
        OBJECTIVE, {"observed_mean": 450.0}, {"iterations": []}
    )
    assert evaluation["result"] == "FAIL_LOW"
    assert evaluation["final_state"] == "REPAIR"
    assert repair["action"] == "heat_flux_scale"
    assert repair["next_heat_flux_scale"] > repair["current_heat_flux_scale"]


def test_eval_repair_tool_returns_fail_high_and_scale_decrease():
    evaluation, repair = EvalRepairTool().evaluate(
        OBJECTIVE, {"observed_mean": 550.0}, {"iterations": []}
    )
    assert evaluation["result"] == "FAIL_HIGH"
    assert evaluation["final_state"] == "REPAIR"
    assert repair["next_heat_flux_scale"] < repair["current_heat_flux_scale"]


def test_eval_repair_tool_returns_fail_stop_for_max_iterations():
    history = {
        "iterations": [
            {"parameters": {"heat_flux_scale": 1.0}},
            {"parameters": {"heat_flux_scale": 1.1}},
            {"parameters": {"heat_flux_scale": 1.2}},
        ]
    }
    evaluation, repair = EvalRepairTool().evaluate(OBJECTIVE, {"observed_mean": 450.0}, history)
    assert evaluation["result"] == "FAIL_STOP"
    assert evaluation["final_state"] == "FAIL_STOP"
    assert repair["allowed"] is False

