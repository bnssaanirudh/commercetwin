import pytest
from app.buyers.agent import BaseBuyerAgent
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState
from app.models import Product
from app.payments.razorpay_client import RazorpayService
from app.chaos.payment_chaos import PaymentChaosAdapter
from app.payments.config import settings

class MockBuyerAgent(BaseBuyerAgent):
    def discover_candidates(self):
        p = Product(sku="SKU-1", merchant_id="test", title="Test Product", category="Test")
        p.price_paise = 1000
        return [p]
        
    def evaluate_candidates(self, products):
        return products
        
    def select_cart(self):
        p = Product(sku="SKU-1", merchant_id="test", title="Test Product", category="Test")
        # Runner explicitly checks price_paise on the item object in the current implementation
        p.price_paise = 1000
        return [p]

class MockRazorpayService(RazorpayService):
    def __init__(self):
        pass # Override init to avoid key checks in this mock
        
    def create_order(self, amount_paise: int, receipt: str, notes: dict = None) -> dict:
        self.created_order = {"id": "order_mock_123", "amount": amount_paise, "receipt": receipt}
        return self.created_order
        
    def fetch_orders_by_receipt(self, receipt_id: str) -> list:
        # Simulate that the server successfully saved the order
        if getattr(self, 'created_order', None) and self.created_order["receipt"] == receipt_id:
            return [self.created_order]
        return []

def test_lost_response_prevents_duplicate_order():
    """
    Tests that a dropped response after successful order creation correctly triggers
    reconciliation and prevents blindly retrying/duplicating the order.
    """
    agent = MockBuyerAgent(intent="test", products=[], attributes_map={})
    
    inventory_db = {"SKU-1": 10}
    pricing_db = {"SKU-1": 1000}
    merchant_policy_db = {"shipping_available": True, "flat_shipping_paise": 0}
    
    mock_service = MockRazorpayService()
    chaos_adapter = PaymentChaosAdapter(mock_service)
    
    runner = CommerceRunner(
        agent=agent,
        inventory_db=inventory_db,
        pricing_db=pricing_db,
        merchant_policy_db=merchant_policy_db,
        chaos_engine=None,
        payment_adapter=chaos_adapter
    )
    
    # Run to precheck
    runner.run_to_precheck()
    if runner.state_machine.current_state == CommerceState.ABORTED:
        print("ABORT REASON:", runner.state_machine.trace_events[-1])
    assert runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT
    
    # Inject fault: The request will succeed on the server, but the network drops the response
    chaos_adapter.inject_fault("DROP_RESPONSE_AFTER_SUCCESS")
    
    # Process payment
    runner.process_payment(receipt_id="test_receipt_drop_1")
    
    # Verify state progression
    events = [e["event_type"] for e in runner.state_machine.trace_events]
    states = [e["payload"]["state"] for e in runner.state_machine.trace_events if e["event_type"] == "STATE_ENTERED"]
    
    assert CommerceState.PAYMENT.value in states
    assert CommerceState.AMBIGUOUS_REMOTE_STATE.value in states
    assert CommerceState.RECONCILIATION_REQUIRED.value in states
    assert CommerceState.RECOVERED_SUCCESS.value in states
    assert CommerceState.COMPLETED.value in states
    assert CommerceState.ABORTED.value not in states
    
    # Ensure the recovered order ID is exactly the one created during the "dropped" request
    recovered_event = [e for e in runner.state_machine.trace_events if e["payload"].get("state") == CommerceState.RECOVERED_SUCCESS.value][0]
    assert recovered_event["payload"]["details"]["recovered_order_id"] == "order_mock_123"
