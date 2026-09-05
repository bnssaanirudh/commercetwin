from app.chaos.catalog_chaos import apply_catalog_chaos
from app.models import Product


def test_catalog_chaos():
    products = [Product(sku="SKU-1", title="Title 1", category="cat1")]
    injections = apply_catalog_chaos(products, 42)
    assert len(injections) > 0
    assert injections[0].family == "catalog"
