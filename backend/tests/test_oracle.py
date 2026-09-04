import pytest
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.buyers.oracle import IntentOracle
from app.models import Product, ProductAttribute

@pytest.fixture
def base_intent():
    return BuyerIntentSchema(
        intent_id="test_001",
        raw_intent="I need a 65W charger and a cable, under 3000 rupees total.",
        hard_constraints=HardConstraints(
            required_categories=["usb_c_chargers", "cables"],
            forbidden_categories=["keyboards"],
            min_attributes={"wattage": 65},
            compatibility={"connector": "USB-C"}
        ),
        soft_preferences=SoftPreferences(),
        target_budget_paise=250000,
        max_budget_paise=300000,
        autonomy_level="autonomous",
        seed=42
    )

@pytest.fixture
def oracle(base_intent):
    return IntentOracle(base_intent)

def test_sku_valid_evaluation(oracle):
    prod = Product(sku="CHG-1", category="usb_c_chargers")
    attrs = [
        ProductAttribute(sku="CHG-1", key="wattage", value="65W", type="string"),
        ProductAttribute(sku="CHG-1", key="connector", value="USB-C", type="string")
    ]
    res = oracle.evaluate_sku(prod, attrs)
    assert res.is_valid

def test_sku_forbidden_category(oracle):
    prod = Product(sku="KBD-1", category="keyboards")
    res = oracle.evaluate_sku(prod, [])
    assert not res.is_valid
    assert res.reason_code == "FORBIDDEN_CATEGORY_PRESENT"

def test_sku_min_attribute_not_met(oracle):
    prod = Product(sku="CHG-2", category="usb_c_chargers")
    attrs = [
        ProductAttribute(sku="CHG-2", key="wattage", value="30W", type="string"),
        ProductAttribute(sku="CHG-2", key="connector", value="USB-C", type="string")
    ]
    res = oracle.evaluate_sku(prod, attrs)
    assert not res.is_valid
    assert res.reason_code == "MIN_ATTRIBUTE_NOT_MET"

def test_sku_compatibility_mismatch(oracle):
    prod = Product(sku="CBL-1", category="cables")
    attrs = [
        ProductAttribute(sku="CBL-1", key="wattage", value="65W", type="string"),
        ProductAttribute(sku="CBL-1", key="connector", value="Lightning", type="string")
    ]
    res = oracle.evaluate_sku(prod, attrs)
    assert not res.is_valid
    assert res.reason_code == "COMPATIBILITY_MISMATCH"

def test_cart_valid(oracle):
    prods = [
        Product(sku="CHG-1", category="usb_c_chargers"),
        Product(sku="CBL-1", category="cables")
    ]
    res = oracle.evaluate_cart(prods, total_amount_paise=280000)
    assert res.is_valid

def test_cart_budget_exceeded(oracle):
    prods = [
        Product(sku="CHG-1", category="usb_c_chargers"),
        Product(sku="CBL-1", category="cables")
    ]
    res = oracle.evaluate_cart(prods, total_amount_paise=350000)
    assert not res.is_valid
    assert res.reason_code == "MAX_BUDGET_EXCEEDED"

def test_cart_missing_required_category(oracle):
    prods = [
        Product(sku="CHG-1", category="usb_c_chargers")
    ] # Missing cable
    res = oracle.evaluate_cart(prods, total_amount_paise=100000)
    assert not res.is_valid
    assert res.reason_code == "MISSING_REQUIRED_CATEGORY"

def test_cart_forbidden_category(oracle):
    prods = [
        Product(sku="CHG-1", category="usb_c_chargers"),
        Product(sku="CBL-1", category="cables"),
        Product(sku="KBD-1", category="keyboards") # Forbidden
    ]
    res = oracle.evaluate_cart(prods, total_amount_paise=280000)
    assert not res.is_valid
    assert res.reason_code == "FORBIDDEN_CATEGORY_PRESENT"
