from __future__ import annotations


def max_iterations_reached(parameter_history: dict, max_iterations: int) -> bool:
    iterations = parameter_history.get("iterations", [])
    return len(iterations) >= max_iterations

