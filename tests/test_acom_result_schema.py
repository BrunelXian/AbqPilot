from __future__ import annotations

from abqpilot.acom.result_schema import empty_structured_result, unsafe_safety_flags, validate_structured_result


def test_output_contract_validates_structured_result_shape():
    result = empty_structured_result("task", "handoff")
    valid, errors = validate_structured_result(result)
    assert valid, errors


def test_result_schema_rejects_unsafe_safety_flags():
    result = empty_structured_result("task", "handoff")
    result["safety_flags"]["solver_started"] = True
    assert unsafe_safety_flags(result) == ["solver_started"]
