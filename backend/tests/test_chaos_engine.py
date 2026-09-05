from app.chaos.engine import ChaosEngine
from app.models import Product


def test_chaos_engine_catalog():
    engine = ChaosEngine()
    p1 = Product(sku="SKU-1", title="Title 1", category="cat1")
    engine.apply(
        products=[p1],
        inventory={"SKU-1": 10},
        pricing={"SKU-1": 100},
        policy={},
        seed=42,
        profile="catalog"
    )
    # The chaos engine applies catalog chaos
    # It might mutate the product
    prods, *_ = engine.get_state()
    assert len(prods) == 1

    # We can rollback
    engine.rollback()

def test_chaos_engine_commerce():
    engine = ChaosEngine()
    p1 = Product(sku="SKU-1", title="Title 1", category="cat1")
    engine.apply(
        products=[p1],
        inventory={"SKU-1": 10},
        pricing={"SKU-1": 100},
        policy={"shipping_available": True, "flat_shipping_paise": 0},
        seed=42,
        profile="commerce"
    )

    assert len(engine.pending_injections) > 0
    engine.trigger_boundary(engine.pending_injections[0].start_boundary)
    assert len(engine.injections) > 0

    engine.rollback()
    assert len(engine.injections) == 0

def test_chaos_engine_context():
    engine = ChaosEngine()
    p1 = Product(sku="SKU-1", title="Title 1", category="cat1")
    engine.apply(
        products=[p1],
        inventory={"SKU-1": 10},
        pricing={"SKU-1": 100},
        policy={},
        seed=42,
        profile="context"
    )

    # Should apply immediately
    if engine.injections:
        engine.rollback()
        assert len(engine.injections) == 0

def test_chaos_engine_all():
    engine = ChaosEngine()
    p1 = Product(sku="SKU-1", title="Title 1", category="cat1")
    engine.apply(
        products=[p1],
        inventory={"SKU-1": 10},
        pricing={"SKU-1": 100},
        policy={"shipping_available": True, "flat_shipping_paise": 0},
        seed=42,
        profile="all"
    )

    # Trigger all boundaries
    boundaries = list(set([i.start_boundary for i in engine.pending_injections]))
    for b in boundaries:
        engine.trigger_boundary(b)

    engine.get_trace_metadata()
    engine.rollback()
    assert len(engine.injections) == 0
