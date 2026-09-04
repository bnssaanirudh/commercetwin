import copy
import random
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models import Product

class ChaosInjection(BaseModel):
    chaos_id: str
    family: str  # context, catalog, inventory_price, commerce_checkout, payment
    target: str
    severity: str
    seed: int
    before_state: Any
    mutated_state: Any
    reversible_patch: Any
    start_boundary: str
    end_boundary: str

class ChaosEngine:
    def __init__(self):
        self.injections: List[ChaosInjection] = []
        
        # We hold the cloned state internally so we don't mutate canonical objects
        self.cloned_products: List[Product] = []
        self.cloned_inventory: Dict[str, int] = {}
        self.cloned_pricing: Dict[str, int] = {}
        self.cloned_policy: Dict[str, Any] = {}

    def _clone_state(self, products: List[Product], inventory: Dict[str, int], 
                     pricing: Dict[str, int], policy: Dict[str, Any]):
        # Deep copy to ensure safety
        self.cloned_products = copy.deepcopy(products)
        self.cloned_inventory = copy.deepcopy(inventory)
        self.cloned_pricing = copy.deepcopy(pricing)
        self.cloned_policy = copy.deepcopy(policy)
        
    def apply(self, products: List[Product], inventory: Dict[str, int], 
              pricing: Dict[str, int], policy: Dict[str, Any], seed: int, profile: str):
        """Applies chaos mutations deterministically to a cloned state."""
        self._clone_state(products, inventory, pricing, policy)
        self.injections = []
        random.seed(seed)
        
        from app.chaos.context_chaos import apply_context_chaos
        from app.chaos.catalog_chaos import apply_catalog_chaos
        from app.chaos.commerce_chaos import apply_commerce_chaos
        
        self.pending_injections = []
        
        if profile in ["catalog", "all"]:
            self.injections.extend(apply_catalog_chaos(self.cloned_products, seed))
        if profile in ["context", "all"]:
            self.injections.extend(apply_context_chaos(self.cloned_products, seed))
        if profile in ["commerce", "all"]:
            self.pending_injections.extend(apply_commerce_chaos(
                self.cloned_products, self.cloned_inventory, self.cloned_pricing, self.cloned_policy, seed
            ))
            
    def trigger_boundary(self, boundary_name: str):
        """Applies dynamic mid-flight injections when a specific state boundary is crossed."""
        triggered = [inj for inj in self.pending_injections if inj.start_boundary == boundary_name]
        for inj in triggered:
            if inj.family == "inventory":
                self.cloned_inventory[inj.reversible_patch["sku"]] = inj.mutated_state["stock"]
            elif inj.family == "price":
                self.cloned_pricing[inj.reversible_patch["sku"]] = inj.mutated_state["price_paise"]
            elif inj.family == "checkout":
                self.cloned_policy[inj.reversible_patch["key"]] = inj.mutated_state[inj.reversible_patch["key"]]
            
            self.injections.append(inj)
            self.pending_injections.remove(inj)

    def rollback(self):
        """Reverses all injections using the reversible_patch field to restore the clone to clean state."""
        # Reverse in reverse order
        for inj in reversed(self.injections):
            if inj.family in ["catalog", "context"]:
                idx = inj.reversible_patch["index"]
                if "field" in inj.reversible_patch:
                    # Catalog generic rollback
                    setattr(self.cloned_products[idx], inj.reversible_patch["field"], inj.reversible_patch["value"])
                else:
                    # Context description rollback
                    self.cloned_products[idx].description = inj.reversible_patch["description"]
            elif inj.family in ["inventory_price", "price"]:
                sku = inj.reversible_patch["sku"]
                self.cloned_pricing[sku] = inj.reversible_patch["price_paise"]
            elif inj.family == "inventory":
                sku = inj.reversible_patch["sku"]
                self.cloned_inventory[sku] = inj.reversible_patch["stock"]
            elif inj.family == "checkout":
                key = inj.reversible_patch["key"]
                self.cloned_policy[key] = inj.reversible_patch["value"]
        
        self.injections = []

    def get_state(self):
        """Returns the mutated clones."""
        return self.cloned_products, self.cloned_inventory, self.cloned_pricing, self.cloned_policy

    def get_trace_metadata(self) -> List[Dict[str, Any]]:
        """Format matching TraceRecorder needs"""
        return [inj.model_dump() for inj in self.injections]
