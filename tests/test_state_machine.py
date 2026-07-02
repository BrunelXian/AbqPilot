import pytest

from abqpilot.core.state_machine import State, StateMachine, StateTransitionError


def test_state_machine_accepts_legal_transitions():
    sm = StateMachine()
    sm.transition(State.INPUT_READY)
    sm.transition(State.INVENTORY_READY)
    sm.transition(State.OBJECTIVE_READY)
    assert sm.current == State.OBJECTIVE_READY


def test_state_machine_rejects_illegal_transitions():
    sm = StateMachine()
    with pytest.raises(StateTransitionError):
        sm.transition(State.JOB_REQUEST_READY)

