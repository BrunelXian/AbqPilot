from __future__ import annotations

from abqpilot.core.stop_rules import max_iterations_reached


class EvalRepairTool:
    def evaluate(self, objective_spec: dict, odb_metrics: dict, parameter_history: dict) -> tuple[dict, dict]:
        target_min, target_max = objective_spec["target_range"]
        target_mid = (float(target_min) + float(target_max)) / 2.0
        max_iterations = int(objective_spec.get("stop_rules", {}).get("max_iterations", 1))
        current_scale = _current_heat_flux_scale(objective_spec, parameter_history)

        evaluation = {
            "tool": "EvalRepairTool",
            "target_min": float(target_min),
            "target_max": float(target_max),
            "observed_mean": odb_metrics.get("observed_mean"),
            "result": "FAIL_STOP",
            "final_state": "FAIL_STOP",
            "errors": [],
        }
        repair_plan = {
            "tool": "EvalRepairTool",
            "action": None,
            "allowed": False,
            "current_heat_flux_scale": current_scale,
            "next_heat_flux_scale": None,
            "reason": None,
        }

        observed = odb_metrics.get("observed_mean")
        if not isinstance(observed, (int, float)):
            evaluation["errors"].append("observed_mean missing or invalid")
            repair_plan["reason"] = "invalid_metrics"
            return evaluation, repair_plan
        observed = float(observed)

        if current_scale <= 0:
            evaluation["errors"].append("heat_flux_scale must be positive")
            repair_plan["reason"] = "invalid_heat_flux_scale"
            return evaluation, repair_plan

        if float(target_min) <= observed <= float(target_max):
            evaluation["result"] = "PASS"
            evaluation["final_state"] = "PASS"
            repair_plan["reason"] = "temperature_in_range"
            return evaluation, repair_plan

        if max_iterations_reached(parameter_history, max_iterations):
            evaluation["result"] = "FAIL_STOP"
            evaluation["final_state"] = "FAIL_STOP"
            evaluation["errors"].append("max iterations reached")
            repair_plan["reason"] = "max_iterations_reached"
            return evaluation, repair_plan

        if observed <= 0:
            evaluation["errors"].append("observed_mean must be positive for scale planning")
            repair_plan["reason"] = "invalid_observed_mean"
            return evaluation, repair_plan

        raw_next = current_scale * (target_mid / observed)
        next_scale = min(max(raw_next, current_scale * 0.8), current_scale * 1.25)
        if next_scale <= 0:
            evaluation["errors"].append("next heat_flux_scale would be non-positive")
            repair_plan["reason"] = "invalid_next_heat_flux_scale"
            return evaluation, repair_plan

        if observed < float(target_min):
            evaluation["result"] = "FAIL_LOW"
            next_scale = max(next_scale, current_scale * 1.01)
            repair_plan["reason"] = "observed_mean_below_target"
        else:
            evaluation["result"] = "FAIL_HIGH"
            next_scale = min(next_scale, current_scale * 0.99)
            repair_plan["reason"] = "observed_mean_above_target"

        evaluation["final_state"] = "REPAIR"
        repair_plan.update(
            {
                "action": "heat_flux_scale",
                "allowed": True,
                "next_heat_flux_scale": round(next_scale, 8),
            }
        )
        return evaluation, repair_plan


def _current_heat_flux_scale(objective_spec: dict, parameter_history: dict) -> float:
    iterations = parameter_history.get("iterations", [])
    if iterations:
        latest = iterations[-1]
        parameters = latest.get("parameters", latest)
        if "heat_flux_scale" in parameters:
            return float(parameters["heat_flux_scale"])
    return float(objective_spec.get("initial_parameters", {}).get("heat_flux_scale", 1.0))

