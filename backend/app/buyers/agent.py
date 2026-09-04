import abc
from typing import List, Dict, Any, Tuple
from .schemas import BuyerIntentSchema
from .oracle import IntentOracle
from app.models import Product, ProductAttribute

class BaseBuyerAgent(abc.ABC):
    def __init__(self, intent: BuyerIntentSchema, products: List[Product], attributes_map: Dict[str, List[ProductAttribute]]):
        self.intent = intent
        self.products = products
        self.attributes_map = attributes_map
        self.oracle = IntentOracle(intent)
        self.trace_events: List[Dict[str, Any]] = []

    def log_trace(self, event_type: str, details: Any):
        self.trace_events.append({"event_type": event_type, "details": details})

    @abc.abstractmethod
    def discover_candidates(self) -> List[Product]:
        """Returns a ranked list of candidate products."""
        pass

    def evaluate_candidates(self, candidates: List[Product]) -> List[Product]:
        valid_products = []
        for p in candidates:
            res = self.oracle.evaluate_sku(p, self.attributes_map.get(p.sku, []))
            if res.is_valid:
                valid_products.append(p)
            else:
                self.log_trace("CANDIDATE_REJECTED", {"sku": p.sku, "reason_code": res.reason_code})
        return valid_products

    def select_cart(self) -> List[Product]:
        self.log_trace("BUYER_STARTED", {"intent_id": self.intent.intent_id})
        
        candidates = self.discover_candidates()
        self.log_trace("CANDIDATES_DISCOVERED", {"skus": [p.sku for p in candidates]})
        
        valid_products = self.evaluate_candidates(candidates)
        
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
