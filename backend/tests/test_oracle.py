from app.buyers.oracle import IntentOracle
from app.buyers.schemas import HardConstraints, BuyerIntentSchema, SoftPreferences
from app.models import Product, ProductAttribute

def test_intent_oracle_evaluate_sku():
    intent = BuyerIntentSchema(
        intent_id="test",
        raw_intent="I want a laptop",
        hard_constraints=HardConstraints(
            required_categories=["electronics"], 
            forbidden_categories=["clothing"],
            max_budget_paise=100000,
            required_attributes={"ram": "16GB"},
            forbidden_attributes={"brand": ["cheap"]},
            min_attributes={"rating": 4.0},
            compatibility={"os": "Windows"}
        ),
        soft_preferences=SoftPreferences(),
        target_budget_paise=50000,
        max_budget_paise=100000,
        autonomy_level="autonomous",
        seed=42
    )
    
    p = Product(sku="TEST", title="Laptop", category="electronics")
    attrs = [
        ProductAttribute(sku="TEST", key="ram", value="16GB", type="string"),
        ProductAttribute(sku="TEST", key="brand", value="good", type="string"),
        ProductAttribute(sku="TEST", key="rating", value="4.5", type="float"),
        ProductAttribute(sku="TEST", key="os", value="Windows 11", type="string")
    ]
    oracle = IntentOracle(intent)
    
    res = oracle.evaluate_sku(p, attrs)
    assert res.is_valid is True
    
    # Missing required attribute
    bad_attrs1 = [ProductAttribute(sku="TEST", key="rating", value="4.5", type="float")]
    res = oracle.evaluate_sku(p, bad_attrs1)
    assert res.is_valid is False
    assert res.reason_code == "MISSING_REQUIRED_ATTRIBUTE"

    # Forbidden category
    p_bad = Product(sku="BAD", title="Shirt", category="clothing")
    res = oracle.evaluate_sku(p_bad, attrs)
    assert res.is_valid is False
    assert res.reason_code == "FORBIDDEN_CATEGORY_PRESENT"

    # Forbidden attribute
    bad_attrs2 = [
        ProductAttribute(sku="TEST", key="ram", value="16GB", type="string"),
        ProductAttribute(sku="TEST", key="brand", value="cheap", type="string")
    ]
    res = oracle.evaluate_sku(p, bad_attrs2)
    assert res.is_valid is False
    assert res.reason_code == "FORBIDDEN_ATTRIBUTE_PRESENT"

    # Below min
    bad_attrs3 = [
        ProductAttribute(sku="TEST", key="ram", value="16GB", type="string"),
        ProductAttribute(sku="TEST", key="rating", value="3.0", type="float")
    ]
    res = oracle.evaluate_sku(p, bad_attrs3)
    assert res.is_valid is False
    assert res.reason_code == "MIN_ATTRIBUTE_NOT_MET"

    # Invalid float parsing
    bad_attrs4 = [
        ProductAttribute(sku="TEST", key="ram", value="16GB", type="string"),
        ProductAttribute(sku="TEST", key="rating", value="not_a_number", type="string")
    ]
    res = oracle.evaluate_sku(p, bad_attrs4)
    assert res.is_valid is False
    assert res.reason_code == "INVALID_ATTRIBUTE_FORMAT"

    # Compatibility
    bad_attrs5 = [
        ProductAttribute(sku="TEST", key="ram", value="16GB", type="string"),
        ProductAttribute(sku="TEST", key="rating", value="4.5", type="float"),
        ProductAttribute(sku="TEST", key="os", value="macOS", type="string")
    ]
    res = oracle.evaluate_sku(p, bad_attrs5)
    assert res.is_valid is False
    assert res.reason_code == "COMPATIBILITY_MISMATCH"

def test_intent_oracle_evaluate_cart():
    intent = BuyerIntentSchema(
        intent_id="test",
        raw_intent="test",
        hard_constraints=HardConstraints(
            required_categories=["electronics"],
            forbidden_categories=["clothing"]
        ),
        soft_preferences=SoftPreferences(),
        target_budget_paise=50000,
        max_budget_paise=100000,
        autonomy_level="autonomous",
        seed=42
    )
    oracle = IntentOracle(intent)
    
    p = Product(sku="TEST", title="Laptop", category="electronics")
    
    res = oracle.evaluate_cart([p], 50000)
    assert res.is_valid is True
    
    res = oracle.evaluate_cart([p], 150000)
    assert res.is_valid is False
    assert res.reason_code == "MAX_BUDGET_EXCEEDED"

    p2 = Product(sku="SHIRT", title="Shirt", category="clothing")
    res = oracle.evaluate_cart([p, p2], 50000)
    assert res.is_valid is False
    assert res.reason_code == "FORBIDDEN_CATEGORY_PRESENT"

    res = oracle.evaluate_cart([p2], 50000)
    assert res.is_valid is False
    assert res.reason_code == "FORBIDDEN_CATEGORY_PRESENT"
