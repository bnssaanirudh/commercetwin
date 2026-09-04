from copy import deepcopy
from typing import Callable, Dict, Any, List
from app.commerce.runner import CommerceRunner, CommerceState

class CausalLocalizer:
    """
    Upgrades failure diagnosis from correlation to controlled counterfactual localization.
    Uses deterministic replays to test one targeted factor change at a time.
    """
    
    def __init__(self, runner_factory: Callable[[], CommerceRunner], 
                 base_inventory: dict, 
                 base_pricing: dict,
                 base_policy: dict):
        self.runner_factory = runner_factory
        self.base_inventory = base_inventory
        self.base_pricing = base_pricing
        self.base_policy = base_policy
        
    def _run_variant(self, inventory=None, pricing=None, policy=None, sku_to_evaluate=None) -> CommerceState:
        """Runs the runner with specific DB states and returns the final state."""
        runner = self.runner_factory()
        
        # Inject the modified states
        if inventory is not None:
            runner.inventory_db = inventory
        if pricing is not None:
            runner.pricing_db = pricing
        if policy is not None:
            runner.merchant_policy_db = policy
            
        runner.run_to_precheck()
        
        if runner.state_machine.current_state == CommerceState.READY_FOR_PAYMENT:
            # For simplicity in testing counterfactuals, if we make it to payment,
            # we run it. Note: in a real causal test, we might skip actual payment
            # or use a mock adapter.
            runner.process_payment()
            
        return runner.state_machine.current_state

    def localize(self, failure_reason: str, failed_sku: str = None) -> dict:
        """
        Attempts to localize the cause of a failure by testing hypotheses.
        """
        # Baseline execution to verify it fails
        baseline_state = self._run_variant(self.base_inventory, self.base_pricing, self.base_policy)
        
        if baseline_state != CommerceState.ABORTED:
            return {
                "hypothesis": "Baseline did not fail",
                "confidence": "NONE"
            }
            
        hypotheses = []
        
        # Test Inventory
        if failure_reason in ["INVENTORY_ZERO", "STALE_INVENTORY"] and failed_sku:
            inv_variant = deepcopy(self.base_inventory)
            inv_variant[failed_sku] = 10  # Restore stock
            
            outcome = self._run_variant(inventory=inv_variant)
            hypotheses.append({
                "hypothesis": "stale inventory",
                "intervention": f"restore stock for {failed_sku} to 10",
                "before_outcome": baseline_state.value,
                "after_outcome": outcome.value,
                "effect_size": "resolved" if outcome != CommerceState.ABORTED else "none"
            })
            
        # Test Pricing
        if failure_reason in ["PRICE_MISMATCH", "STALE_PRICE"] and failed_sku:
            # We assume the agent expected a different price. 
            # We don't have the agent's expected price directly here, but we can 
            # simulate an intervention by artificially bypassing the price check or 
            # aligning the DB to a known "old" price.
            # In a real scenario, we'd extract the expected price from the agent's cart.
            # For this localizer, we'll try to align the DB price to the agent's cart price.
            # We can peek at the runner's cart to find what it wanted.
            peek_runner = self.runner_factory()
            peek_runner.inventory_db = self.base_inventory
            peek_runner.pricing_db = self.base_pricing
            peek_runner.run_to_precheck() # it will abort, but cart is populated
            
            agent_price = None
            for item in peek_runner.cart:
                if item.sku == failed_sku:
                    agent_price = getattr(item, 'price_paise', 0)
                    break
                    
            if agent_price is not None:
                price_variant = deepcopy(self.base_pricing)
                price_variant[failed_sku] = agent_price
                
                outcome = self._run_variant(pricing=price_variant)
                hypotheses.append({
                    "hypothesis": "price drift",
                    "intervention": f"align canonical DB price for {failed_sku} to {agent_price}",
                    "before_outcome": baseline_state.value,
                    "after_outcome": outcome.value,
                    "effect_size": "resolved" if outcome != CommerceState.ABORTED else "none"
                })

        # Test Missing Attribute (NO_VALID_PRODUCTS_FOUND)
        if failure_reason == "NO_VALID_PRODUCTS_FOUND":
            # For attribute matching, we'd intervene in the Agent's product catalog.
            # In this simple implementation, we just mock the intervention.
            pass
            
        # Analyze results
        resolved_hypotheses = [h for h in hypotheses if h["effect_size"] == "resolved"]
        
        if len(resolved_hypotheses) == 1:
            best = resolved_hypotheses[0]
            best["confidence"] = "HIGH"
            best["alternative_explanations"] = []
            return best
        elif len(resolved_hypotheses) > 1:
            return {
                "hypothesis": "Multiple factors resolved failure",
                "confidence": "LOW",
                "alternative_explanations": [h["hypothesis"] for h in resolved_hypotheses]
            }
        else:
            return {
                "hypothesis": "Unknown or Multi-factor",
                "confidence": "LOW",
                "alternative_explanations": ["Interventions did not resolve the failure independently"]
            }
