import pytest
import copy
from app.models import Product
from app.chaos.engine import ChaosEngine

@pytest.fixture
def clean_data():
    p1 = Product(sku="SKU-1", category="cables", title="Cable", description="A cable")
    p1.price_paise = 1000
    
    p2 = Product(sku="SKU-2", category="adapters", title="Adapter", description="An adapter")
    p2.price_paise = 2000
    
    products = [p1, p2]
    inventory = {"SKU-1": 10, "SKU-2": 5}
    pricing = {"SKU-1": 1000, "SKU-2": 2000}
    policy = {"shipping_available": True}
    
    # Store deepcopy strictly for equality tests
    return products, inventory, pricing, policy, copy.deepcopy(products), copy.deepcopy(inventory), copy.deepcopy(pricing)

def test_determinism(clean_data):
    products, inventory, pricing, policy, _, _, _ = clean_data
    
    engine1 = ChaosEngine()
    engine1.apply(products, inventory, pricing, policy, seed=123, profile="catalog")
    
    engine2 = ChaosEngine()
    engine2.apply(products, inventory, pricing, policy, seed=123, profile="catalog")
    
    # Exactly same chaos injections should occur
    assert engine1.injections[0].target == engine2.injections[0].target
    assert engine1.injections[0].mutated_state == engine2.injections[0].mutated_state

def test_data_safety(clean_data):
    products, inventory, pricing, policy, base_p, base_i, base_pr = clean_data
    
    engine = ChaosEngine()
    engine.apply(products, inventory, pricing, policy, seed=42, profile="catalog")
    
    # Ensure the original `products` list passed in was NOT mutated
    assert products[0].description == base_p[0].description
    assert products[0].title == base_p[0].title
    assert products[1].description == base_p[1].description
    assert products[1].title == base_p[1].title
    
    # The mutated clones SHOULD be different (at least one)
    clones, _, _, _ = engine.get_state()
    differences = sum(1 for i in range(2) if clones[i].description != base_p[i].description or clones[i].title != base_p[i].title or clones[i].category != base_p[i].category)
    assert differences > 0

def test_rollback_integrity(clean_data):
    products, inventory, pricing, policy, base_p, base_i, base_pr = clean_data
    
    engine = ChaosEngine()
    engine.apply(products, inventory, pricing, policy, seed=99, profile="standard")
    
    clones, c_inv, c_pricing, _ = engine.get_state()
    # At least one price was mutated
    assert c_pricing != base_pr
    
    engine.rollback()
    
    clones_after, c_inv_after, c_pricing_after, _ = engine.get_state()
    
    # Must be perfectly restored
    assert c_pricing_after == base_pr
    assert len(engine.injections) == 0

def test_trace_formatting(clean_data):
    products, inventory, pricing, policy, _, _, _ = clean_data
    
    engine = ChaosEngine()
    engine.apply(products, inventory, pricing, policy, seed=1, profile="catalog")
    
    trace_meta = engine.get_trace_metadata()
    assert isinstance(trace_meta, list)
    assert len(trace_meta) > 0
    
    inj = trace_meta[0]
    assert "chaos_id" in inj
    assert "before_state" in inj
    assert "reversible_patch" in inj
