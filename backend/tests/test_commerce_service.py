from app.commerce.runner import CommerceRunner, CommerceState
from app.models import Product, TraceEvent, TransactionTrace
from app.services.commerce_service import CommerceService


class MockAgent:
    def __init__(self):
        self.intent = type("Intent", (), {"intent_id": "test-intent", "max_budget_paise": 1000})()
        self.trace_events = [
            {"event_type": "BUYER_STARTED", "details": {"intent_id": "test-intent"}},
            {"event_type": "CART_CREATED", "details": {"skus": ["SKU-1"]}}
        ]

    def discover_candidates(self):
        return []

    def evaluate_candidates(self, candidates):
        from app.models import Product
        p = Product(sku="SKU-1", title="Test", category="test")
        p.price_paise = 100
        return [p]

    def select_cart(self, valid):
        return valid


def test_commerce_service_create_experiment(db_session):
    svc = CommerceService(db_session)
    exp_id = svc.create_experiment({"chaos_profile": "test"})
    assert exp_id.startswith("EXP-")


def test_commerce_service_run_trace(db_session):
    svc = CommerceService(db_session)
    agent = MockAgent()

    runner = svc.run_trace(
        agent=agent,
        inventory_db={"SKU-1": 10},
        pricing_db={"SKU-1": 100},
        merchant_policy_db={"shipping_available": True, "flat_shipping_paise": 0},
        experiment_id="TEST-EXP"
    )

    assert runner is not None
    # Check trace was persisted
    traces = db_session.query(TransactionTrace).all()
    assert len(traces) > 0
    assert traces[0].buyer_id == "test-intent"

    events = db_session.query(TraceEvent).all()
    assert len(events) >= 2


def test_commerce_service_aggregate_metrics(db_session):
    svc = CommerceService(db_session)
    metrics = svc.get_aggregate_metrics()
    assert metrics["Robust_Transaction_Yield"] >= 0.0


def test_commerce_service_localize_failure(db_session):
    svc = CommerceService(db_session)
    agent = MockAgent()
    svc.run_trace(
        agent=agent,
        inventory_db={"SKU-1": 10},
        pricing_db={"SKU-1": 100},
        merchant_policy_db={},
    )
    traces = db_session.query(TransactionTrace).all()
    trace_id = traces[-1].trace_id

    res = svc.localize_failure(trace_id)
    assert res["status"] == "localized"


def test_commerce_service_prepare_payment(db_session):
    svc = CommerceService(db_session)
    agent = MockAgent()
    runner = CommerceRunner(agent, {"SKU-1": 10}, {"SKU-1": 100}, {})

    item = Product(sku="SKU-1", title="Test", category="test")
    item.price_paise = 100
    runner.cart = [item]

    runner.state_machine.transition_to(CommerceState.DISCOVERY)
    runner.state_machine.transition_to(CommerceState.EVALUATION)
    runner.state_machine.transition_to(CommerceState.SELECTION)
    runner.state_machine.transition_to(CommerceState.CART_CREATED, {"skus": ["SKU-1"]})
    runner.state_machine.transition_to(CommerceState.PRECHECK)
    runner.final_total_paise = 100  # set explicitly since we bypassed _execute_prechecks
    runner.state_machine.transition_to(CommerceState.READY_FOR_PAYMENT, {"total_paise": 100})
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT

    class MockPaymentAdapter:
        def create_order(self, amount_paise, receipt):
            return {"id": "order_mock_123", "amount": amount_paise, "currency": "INR"}

    runner.payment_adapter = MockPaymentAdapter()

    # Call prepare_payment (first time)
    svc.prepare_payment(runner, receipt_id="rec_test")

    # Assert state
    assert runner.state_machine.current_state == CommerceState.PAYMENT_PENDING

    # Assert DB has exactly one operation
    from app.models import PaymentOperation
    ops = db_session.query(PaymentOperation).all()
    assert len(ops) == 1
    assert ops[0].amount_paise == 100
    assert ops[0].razorpay_order_id == "order_mock_123"

    # Call prepare_payment again (duplicate) to test idempotency
    # Should not crash, and should not duplicate the row
    svc.prepare_payment(runner, receipt_id="rec_test")
    ops = db_session.query(PaymentOperation).all()
    assert len(ops) == 1
