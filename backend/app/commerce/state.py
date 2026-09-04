import enum
from typing import List, Dict, Any

class CommerceState(enum.Enum):
    INTENT_RECEIVED = "INTENT_RECEIVED"
    DISCOVERY = "DISCOVERY"
    EVALUATION = "EVALUATION"
    SELECTION = "SELECTION"
    CART_CREATED = "CART_CREATED"
    PRECHECK = "PRECHECK"
    READY_FOR_PAYMENT = "READY_FOR_PAYMENT"
    PAYMENT = "PAYMENT"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_SUCCEEDED = "PAYMENT_SUCCEEDED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    AMBIGUOUS_REMOTE_STATE = "AMBIGUOUS_REMOTE_STATE"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RECOVERED_SUCCESS = "RECOVERED_SUCCESS"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"

class InvalidStateTransitionError(Exception):
    pass

class CommerceStateMachine:
    # Define valid transitions
    VALID_TRANSITIONS = {
        CommerceState.INTENT_RECEIVED: [CommerceState.DISCOVERY, CommerceState.ABORTED],
        CommerceState.DISCOVERY: [CommerceState.EVALUATION, CommerceState.ABORTED],
        CommerceState.EVALUATION: [CommerceState.SELECTION, CommerceState.ABORTED],
        CommerceState.SELECTION: [CommerceState.CART_CREATED, CommerceState.ABORTED],
        CommerceState.CART_CREATED: [CommerceState.PRECHECK, CommerceState.ABORTED],
        CommerceState.PRECHECK: [CommerceState.READY_FOR_PAYMENT, CommerceState.ABORTED],
        CommerceState.READY_FOR_PAYMENT: [CommerceState.PAYMENT, CommerceState.ABORTED],
        CommerceState.PAYMENT: [CommerceState.PAYMENT_PENDING, CommerceState.ABORTED, CommerceState.AMBIGUOUS_REMOTE_STATE],
        CommerceState.PAYMENT_PENDING: [CommerceState.PAYMENT_SUCCEEDED, CommerceState.PAYMENT_FAILED, CommerceState.ABORTED],
        CommerceState.PAYMENT_SUCCEEDED: [CommerceState.COMPLETED, CommerceState.RECONCILIATION_REQUIRED],
        CommerceState.PAYMENT_FAILED: [CommerceState.ABORTED, CommerceState.RECONCILIATION_REQUIRED],
        CommerceState.AMBIGUOUS_REMOTE_STATE: [CommerceState.RECONCILIATION_REQUIRED, CommerceState.ABORTED],
        CommerceState.RECONCILIATION_REQUIRED: [CommerceState.RECOVERED_SUCCESS, CommerceState.ABORTED],
        CommerceState.RECOVERED_SUCCESS: [CommerceState.COMPLETED],
        CommerceState.COMPLETED: [],
        CommerceState.ABORTED: []
    }

    def __init__(self):
        self.current_state = CommerceState.INTENT_RECEIVED
        self.trace_events: List[Dict[str, Any]] = []
        self._record_trace("STATE_ENTERED", {"state": self.current_state.value})

    def _record_trace(self, event_type: str, payload: dict):
        self.trace_events.append({
            "event_type": event_type,
            "payload": payload
        })

    def transition_to(self, new_state: CommerceState, payload: dict = None):
        if new_state not in self.VALID_TRANSITIONS.get(self.current_state, []):
            raise InvalidStateTransitionError(f"Cannot transition from {self.current_state.value} to {new_state.value}")
        
        self.current_state = new_state
        self._record_trace("STATE_ENTERED", {"state": self.current_state.value, "details": payload or {}})
