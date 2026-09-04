import pytest
from app.buyers.schemas import BuyerIntentSchema, HardConstraints
from app.models import Product, ProductAttribute
from app.buyers.configurations import StructuredBuyer, SemanticBuyer, HybridBuyer

@pytest.fixture
def mock_catalog():
    # p1: Exactly matches category 'cables', cheap.
    p1 = Product(sku="SKU-1", category="cables", title="Basic Cable", description="A cheap usb cable")
    p1.price_paise = 100
    # p2: Semantic match (title has 'cable'), wrong category 'adapters', expensive.
    p2 = Product(sku="SKU-2", category="adapters", title="Fancy Cable Adapter", description="Expensive cable adapter")
    p2.price_paise = 5000
    # p3: Matches category 'cables', expensive but highly semantic title.
    p3 = Product(sku="SKU-3", category="cables", title="Premium Super Fast Cable", description="The ultimate premium super fast cable for all needs")
    p3.price_paise = 2000
    
    # p4: Impossible item (price too high for budget)
    p4 = Product(sku="SKU-4", category="cables", title="Gold Cable", description="Solid gold cable")
    p4.price_paise = 99999999
    
    return [p1, p2, p3, p4]

@pytest.fixture
def mock_attributes():
    return {
        "SKU-1": [],
        "SKU-2": [],
        "SKU-3": [],
        "SKU-4": []
    }

@pytest.fixture
def intent():
    from app.buyers.schemas import SoftPreferences
    return BuyerIntentSchema(
        intent_id="INT-1",
        raw_intent="I need a premium super fast cable.",
        hard_constraints=HardConstraints(required_categories=["cables"]),
        soft_preferences=SoftPreferences(),
        target_budget_paise=5000,
        max_budget_paise=10000,
        autonomy_level="supervised",
        seed=42
    )

def test_buyer_rankings_differ(intent, mock_catalog, mock_attributes):
    structured = StructuredBuyer(intent, mock_catalog, mock_attributes)
    semantic = SemanticBuyer(intent, mock_catalog, mock_attributes)
    hybrid = HybridBuyer(intent, mock_catalog, mock_attributes)
    
    # Discover candidates
    s_cand = structured.discover_candidates()
    sem_cand = semantic.discover_candidates()
    h_cand = hybrid.discover_candidates()
    
    # Structured ranks by price: SKU-1 should be first
    assert s_cand[0].sku == "SKU-1"
    
    # Semantic ranks by Jaccard similarity to "premium super fast cable". 
    # SKU-3 has all those words. SKU-1 only has "cable".
    assert sem_cand[0].sku == "SKU-3"
    
    # Hybrid also boost category. SKU-3 matches category AND text.
    assert h_cand[0].sku == "SKU-3"
    
    # Note: Semantic might rank SKU-2 above SKU-1 if title words match better,
    # but the key is they rank differently than Structured.
    assert [p.sku for p in s_cand] != [p.sku for p in sem_cand]

def test_buyers_enforce_oracle_and_build_valid_cart(intent, mock_catalog, mock_attributes):
    # Despite differing discovery, all must produce a valid cart according to Oracle
    buyers = [
        StructuredBuyer(intent, mock_catalog, mock_attributes),
        SemanticBuyer(intent, mock_catalog, mock_attributes),
        HybridBuyer(intent, mock_catalog, mock_attributes)
    ]
    
    for buyer in buyers:
        cart = buyer.select_cart()
        assert len(cart) == 1
        assert cart[0].category == "cables" # Must be cables
        assert cart[0].sku != "SKU-4" # Must not be the over-budget one

def test_impossible_intent_terminates_cleanly(mock_catalog, mock_attributes):
    from app.buyers.schemas import SoftPreferences
    impossible_intent = BuyerIntentSchema(
        intent_id="INT-2",
        raw_intent="I need a cable",
        hard_constraints=HardConstraints(required_categories=["cables"], required_attributes={"nonexistent": "val"}),
        soft_preferences=SoftPreferences(),
        target_budget_paise=100,
        max_budget_paise=100,
        autonomy_level="supervised",
        seed=42
    )
    
    buyer = HybridBuyer(impossible_intent, mock_catalog, mock_attributes)
    cart = buyer.select_cart()
    
    # Cart must be empty because nothing matches required_attributes
    assert len(cart) == 0
    
    # Verify trace events recorded the rejections
    rejections = [e for e in buyer.trace_events if e["event_type"] == "CANDIDATE_REJECTED"]
    assert len(rejections) > 0
    assert "MISSING_REQUIRED_ATTRIBUTE" in rejections[0]["details"]["reason_code"]
