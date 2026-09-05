import copy
import random
from typing import Any

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
        self.injections: list[ChaosInjection] = []

        # We hold the cloned state internally so we don't mutate canonical objects
        self.cloned_products: list[Product] = []
        self.cloned_inventory: dict[str, int] = {}
        self.cloned_pricing: dict[str, int] = {}
        self.cloned_policy: dict[str, Any] = {}

    def _clone_state(self, products: list[Product], inventory: dict[str, int],
                     pricing: dict[str, int], policy: dict[str, Any], attributes_map: dict[str, list[Any]] | None = None):
        # Deep copy to ensure safety
        self.cloned_products = copy.deepcopy(products)
        self.cloned_inventory = copy.deepcopy(inventory)
        self.cloned_pricing = copy.deepcopy(pricing)
        self.cloned_policy = copy.deepcopy(policy)
        self.cloned_attributes = copy.deepcopy(attributes_map) if attributes_map is not None else {}

    def apply(self, products: list[Product], inventory: dict[str, int],
              pricing: dict[str, int], policy: dict[str, Any], seed: int, profile: str, attributes_map: dict[str, list[Any]] | None = None):
        """Applies chaos mutations deterministically to a cloned state."""
        self._clone_state(products, inventory, pricing, policy, attributes_map)
        self.injections = []
        random.seed(seed)

        from app.chaos.catalog_chaos import apply_catalog_chaos
        from app.chaos.commerce_chaos import apply_commerce_chaos
        from app.chaos.context_chaos import apply_context_chaos

        self.pending_injections = []

        if profile in ["catalog", "all"]:
            self.injections.extend(apply_catalog_chaos(self.cloned_products, seed))
        if profile in ["context", "all"]:
            self.injections.extend(apply_context_chaos(self.cloned_products, seed))
        if profile in ["commerce", "all"]:
            self.pending_injections.extend(apply_commerce_chaos(
                self.cloned_products, self.cloned_inventory, self.cloned_pricing, self.cloned_policy, seed
            ))
        if profile in ["drop_attribute", "all"]:
            import uuid
            for p in self.cloned_products:
                if p.sku in self.cloned_attributes:
                    attrs = self.cloned_attributes[p.sku]
                    dropped = []
                    kept = []
                    for attr in attrs:
                        if attr.key == "power_watts":
                            dropped.append(attr)
                        else:
                            kept.append(attr)
                    if dropped:
                        self.cloned_attributes[p.sku] = kept
                        self.injections.append(ChaosInjection(
                            chaos_id=f"CHAOS-{uuid.uuid4().hex[:8]}",
                            family="catalog",
                            target=f"{p.sku}_power_watts",
                            severity="high",
                            seed=seed,
                            before_state="present",
                            mutated_state="dropped",
                            reversible_patch={"sku": p.sku, "dropped_attrs": dropped},
                            start_boundary="init",
                            end_boundary="end"
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
        # Reverse in reverse order. IMPORTANT: dropped_attrs branch must be checked
        # before the generic catalog/field branch, since both share family="catalog".
        for inj in reversed(self.injections):
            if inj.family in ["catalog", "context"] and "dropped_attrs" in inj.reversible_patch:
                # Dropped-attribute rollback: restore attrs into cloned_attributes map
                sku = inj.reversible_patch["sku"]
                self.cloned_attributes.setdefault(sku, [])
                existing_keys = {a.key for a in self.cloned_attributes[sku]}
                for attr in inj.reversible_patch["dropped_attrs"]:
                    if attr.key not in existing_keys:
                        self.cloned_attributes[sku].append(attr)
                        existing_keys.add(attr.key)
            elif inj.family in ["catalog", "context"]:
                idx = inj.reversible_patch.get("index", 0)
                if "field" in inj.reversible_patch:
                    # Catalog generic rollback
                    setattr(self.cloned_products[idx], inj.reversible_patch["field"], inj.reversible_patch["value"])
                else:
                    # Context description rollback
                    self.cloned_products[idx].description = inj.reversible_patch.get("description", "")
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
        return self.cloned_products, self.cloned_inventory, self.cloned_pricing, self.cloned_policy, self.cloned_attributes

    def get_trace_metadata(self) -> list[dict[str, Any]]:
        """Format matching TraceRecorder needs"""
        return [inj.model_dump() for inj in self.injections]
