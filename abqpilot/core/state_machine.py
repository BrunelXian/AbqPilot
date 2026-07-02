from __future__ import annotations

from enum import StrEnum


class StateTransitionError(RuntimeError):
    """Raised when a deterministic orchestration transition is illegal."""


class State(StrEnum):
    INIT = "INIT"
    INPUT_READY = "INPUT_READY"
    INVENTORY_READY = "INVENTORY_READY"
    OBJECTIVE_READY = "OBJECTIVE_READY"
    BUILD_REQUEST_READY = "BUILD_REQUEST_READY"
    INP_GENERATED = "INP_GENERATED"
    STATIC_VALIDATED = "STATIC_VALIDATED"
    STATIC_VALIDATION_FAILED = "STATIC_VALIDATION_FAILED"
    DIFF_GUARD_PASSED = "DIFF_GUARD_PASSED"
    DIFF_GUARD_FAILED = "DIFF_GUARD_FAILED"
    PHYSICS_GUARD_PASSED = "PHYSICS_GUARD_PASSED"
    PHYSICS_GUARD_FAILED = "PHYSICS_GUARD_FAILED"
    JOB_REQUEST_READY = "JOB_REQUEST_READY"
    JOB_SUBMITTED = "JOB_SUBMITTED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"
    ODB_EXTRACTED = "ODB_EXTRACTED"
    ODB_MISSING = "ODB_MISSING"
    METRICS_READY = "METRICS_READY"
    EVALUATED = "EVALUATED"
    PASS = "PASS"
    REPAIR = "REPAIR"
    FAIL_STOP = "FAIL_STOP"


LEGAL_TRANSITIONS: dict[State, set[State]] = {
    State.INIT: {State.INPUT_READY},
    State.INPUT_READY: {State.INVENTORY_READY, State.FAIL_STOP},
    State.INVENTORY_READY: {State.OBJECTIVE_READY, State.FAIL_STOP},
    State.OBJECTIVE_READY: {State.BUILD_REQUEST_READY, State.FAIL_STOP},
    State.BUILD_REQUEST_READY: {State.INP_GENERATED, State.FAIL_STOP},
    State.INP_GENERATED: {State.STATIC_VALIDATED, State.STATIC_VALIDATION_FAILED},
    State.STATIC_VALIDATION_FAILED: {State.FAIL_STOP},
    State.STATIC_VALIDATED: {State.DIFF_GUARD_PASSED, State.DIFF_GUARD_FAILED},
    State.DIFF_GUARD_FAILED: {State.FAIL_STOP},
    State.DIFF_GUARD_PASSED: {State.PHYSICS_GUARD_PASSED, State.PHYSICS_GUARD_FAILED},
    State.PHYSICS_GUARD_FAILED: {State.FAIL_STOP},
    State.PHYSICS_GUARD_PASSED: {State.JOB_REQUEST_READY},
    State.JOB_REQUEST_READY: {State.JOB_SUBMITTED, State.ODB_EXTRACTED, State.ODB_MISSING},
    State.JOB_SUBMITTED: {State.JOB_COMPLETED, State.JOB_FAILED},
    State.JOB_FAILED: {State.FAIL_STOP},
    State.JOB_COMPLETED: {State.ODB_EXTRACTED, State.ODB_MISSING},
    State.ODB_MISSING: {State.FAIL_STOP},
    State.ODB_EXTRACTED: {State.METRICS_READY},
    State.METRICS_READY: {State.EVALUATED},
    State.EVALUATED: {State.PASS, State.REPAIR, State.FAIL_STOP},
    State.PASS: set(),
    State.REPAIR: set(),
    State.FAIL_STOP: set(),
}


class StateMachine:
    def __init__(self, initial_state: State = State.INIT) -> None:
        self.current = initial_state
        self.history: list[str] = [initial_state.value]

    def can_transition(self, next_state: State) -> bool:
        return next_state in LEGAL_TRANSITIONS[self.current]

    def transition(self, next_state: State) -> State:
        if not self.can_transition(next_state):
            raise StateTransitionError(
                f"Illegal transition: {self.current.value} -> {next_state.value}"
            )
        self.current = next_state
        self.history.append(next_state.value)
        return self.current

