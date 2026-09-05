import abc
from typing import Any

from app.models import Product, ProductAttribute

from .oracle import IntentOracle
from .schemas import BuyerIntentSchema


class BaseBuyerAgent(abc.ABC):
    def __init__(self, intent: BuyerIntentSchema, products: list[Product], attributes_map: dict[str, list[ProductAttribute]]):
        self.intent = intent
        self.products = products
        self.attributes_map = attributes_map
        self.oracle = IntentOracle(intent)
        self.trace_events: list[dict[str, Any]] = []

    def log_trace(self, event_type: str, details: Any):
        self.trace_events.append({"event_type": event_type, "details": details})

    @abc.abstractmethod
    def discover_candidates(self) -> list[Product]:
        """Returns a ranked list of candidate products."""

    def evaluate_candidates(self, candidates: list[Product]) -> list[Product]:
        valid_products = []
        for p in candidates:
            res = self.oracle.evaluate_sku(p, self.attributes_map.get(p.sku, []))
            if res.is_valid:
                valid_products.append(p)
            else:
                self.log_trace("CANDIDATE_REJECTED", {"sku": p.sku, "reason_code": res.reason_code})
        return valid_products

    def select_cart(self, valid_products: list[Product]) -> list[Product]:
        self.log_trace("BUYER_STARTED", {"intent_id": self.intent.intent_id})

        # Simple greedy cart construction based on ranking (highest ranked valid items)
        cart = []
        total_price = 0
        categories_needed = set(self.intent.hard_constraints.required_categories)

        for p in valid_products:
            if p.category in categories_needed:
                # Add to cart
                cart.append(p)
                total_price += getattr(p, 'price_paise', 0)
                categories_needed.remove(p.category)

            if not categories_needed:
                break

        # Final Oracle Cart Check
        cart_res = self.oracle.evaluate_cart(cart, total_price)
        if not cart_res.is_valid:
            self.log_trace("CART_REJECTED", {"reason_code": cart_res.reason_code})
            return []

        self.log_trace("CART_FINALIZED", {"skus": [p.sku for p in cart]})
        return cart
