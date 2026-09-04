import pytest
from app.analytics.causal import CausalLocalizer
from app.commerce.runner import CommerceRunner
from app.commerce.state import CommerceState
from app.buyers.agent import BaseBuyerAgent
from app.models import Product

class MockBuyerAgent(BaseBuyerAgent):
    def discover_candidates(self):
        p = Product(sku="SKU-1", merchant_id="test", title="Test Product", category="Test")
        p.price_paise = 1000
        return [p]
        
    def evaluate_candidates(self, products):
        return products
        
    def select_cart(self):
        p = Product(sku="SKU-1", merchant_id="test", title="Test Product", category="Test")
        p.price_paise = 1000
        return [p]

def create_runner_factory(inventory_db, pricing_db, policy_db):
    def factory():
        agent = MockBuyerAgent(intent="test", products=[], attributes_map={})
        # Use simple dictionary copies
        return CommerceRunner(
            agent=agent,
            inventory_db=dict(inventory_db),
            pricing_db=dict(pricing_db),
            merchant_policy_db=dict(policy_db)
        )
    return factory

def test_causal_inventory_exhaustion():
    # Base state: Inventory is 0 (exhausted)
    base_inv = {"SKU-1": 0}
    base_price = {"SKU-1": 1000}
    base_policy = {"shipping_available": True, "flat_shipping_paise": 0}
    
    factory = create_runner_factory(base_inv, base_price, base_policy)
    
    localizer = CausalLocalizer(factory, base_inv, base_price, base_policy)
    
    # We know the reason and sku from the trace (simulated)
    result = localizer.localize("INVENTORY_ZERO", "SKU-1")
    
    assert result["hypothesis"] == "stale inventory"
    assert result["confidence"] == "HIGH"
    assert result["effect_size"] == "resolved"
    assert result["before_outcome"] == CommerceState.ABORTED.value
    assert result["after_outcome"] == CommerceState.COMPLETED.value
    assert "alternative_explanations" in result
    assert len(result["alternative_explanations"]) == 0

def test_causal_price_drift():
    # Base state: Price in DB drifted to 1500, but agent thinks it's 1000
    base_inv = {"SKU-1": 10}
    base_price = {"SKU-1": 1500}
    base_policy = {"shipping_available": True, "flat_shipping_paise": 0}
    
    factory = create_runner_factory(base_inv, base_price, base_policy)
    
    localizer = CausalLocalizer(factory, base_inv, base_price, base_policy)
    
    result = localizer.localize("PRICE_MISMATCH", "SKU-1")
    
    assert result["hypothesis"] == "price drift"
    assert result["confidence"] == "HIGH"
    assert result["effect_size"] == "resolved"
    assert result["before_outcome"] == CommerceState.ABORTED.value
    assert result["after_outcome"] == CommerceState.COMPLETED.value

def test_uncertain_multi_factor():
    # Base state: BOTH inventory exhausted AND price drifted
    base_inv = {"SKU-1": 0}
    base_price = {"SKU-1": 1500}
    base_policy = {"shipping_available": True, "flat_shipping_paise": 0}
    
    factory = create_runner_factory(base_inv, base_price, base_policy)
    
    localizer = CausalLocalizer(factory, base_inv, base_price, base_policy)
    
    # We pass INVENTORY_ZERO because that's the first check that fails in runner
    result = localizer.localize("INVENTORY_ZERO", "SKU-1")
    
    # If we only fix inventory, the price check will still fail!
    # Therefore, resolving ONE factor doesn't resolve the transaction.
    assert result["hypothesis"] == "Unknown or Multi-factor"
    assert result["confidence"] == "LOW"
