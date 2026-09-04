from typing import List, Dict, Any
from app.buyers.agent import BaseBuyerAgent
from .state import CommerceStateMachine, CommerceState
from app.models import Product, InventorySnapshot, PricingSnapshot

class CommerceRunnerError(Exception):
    pass

class CommerceRunner:
    def __init__(self, agent: BaseBuyerAgent, 
                 inventory_db: Dict[str, int], 
                 pricing_db: Dict[str, int],
                 merchant_policy_db: Dict[str, Any],
                 chaos_engine=None,
                 payment_adapter=None):
        self.agent = agent
        self.state_machine = CommerceStateMachine()
        
        # Mocks for DB checks to isolate the state machine logic
        self.inventory_db = inventory_db
        self.pricing_db = pricing_db
        self.merchant_policy_db = merchant_policy_db
        self.chaos_engine = chaos_engine
        self.payment_adapter = payment_adapter
        
        self.cart: List[Product] = []
        self.final_total_paise: int = 0
        self.receipt_id: str = None
        
    def _transition_and_trigger(self, state, data=None):
        self.state_machine.transition_to(state, data)
        if self.chaos_engine:
            self.chaos_engine.trigger_boundary(state.name)

    def run_to_precheck(self):
        try:
            # DISCOVERY
            self._transition_and_trigger(CommerceState.DISCOVERY)
            candidates = self.agent.discover_candidates()
            
            # EVALUATION
            self._transition_and_trigger(CommerceState.EVALUATION)
            valid_candidates = self.agent.evaluate_candidates(candidates)
            if not valid_candidates:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "NO_VALID_PRODUCTS_FOUND"})
                return
                
            # SELECTION
            self._transition_and_trigger(CommerceState.SELECTION)
            self.cart = self.agent.select_cart(valid_candidates)
            
            if not self.cart:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "INVALID_CART_CONSTRUCTED"})
                return
                
            # CART CREATED
            self._transition_and_trigger(CommerceState.CART_CREATED, {"skus": [p.sku for p in self.cart]})
            
            # PRECHECK
            self._transition_and_trigger(CommerceState.PRECHECK)
            self._execute_prechecks()
            
            # If we survived prechecks without aborting
            if self.state_machine.current_state != CommerceState.ABORTED:
                self._transition_and_trigger(CommerceState.READY_FOR_PAYMENT, {"total_paise": self.final_total_paise})
                
        except Exception as e:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"UNEXPECTED_ERROR: {str(e)}"})
            raise

    def process_payment(self, receipt_id: str = "receipt_default"):
        """Final checkout validation strictly blocking stale context."""
        if self.state_machine.current_state != CommerceState.READY_FOR_PAYMENT:
            return
            
        self.receipt_id = receipt_id
            
        try:
            self._transition_and_trigger(CommerceState.PAYMENT)
            self._execute_payment_validation()
            
            if self.state_machine.current_state != CommerceState.ABORTED:
                if self.payment_adapter:
                    import requests
                    try:
                        # Attempt to create remote order
                        order = self.payment_adapter.create_order(
                            amount_paise=self.final_total_paise,
                            receipt=self.receipt_id
                        )
                        self._transition_and_trigger(CommerceState.PAYMENT_PENDING, {"order_id": order["id"]})
                        return
                    except requests.exceptions.ReadTimeout:
                        # Network dropout. State is ambiguous.
                        self._transition_and_trigger(CommerceState.AMBIGUOUS_REMOTE_STATE)
                        self._reconcile_ambiguous_payment()
                        return
                    except Exception as e:
                        # Direct failure (e.g., 5xx, or other known hard fails)
                        self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"PAYMENT_ERROR: {str(e)}"})
                        return
                        
                # Either successful remote call, or no adapter used (mock)
                self._transition_and_trigger(CommerceState.PAYMENT_PENDING, {"order_id": "mock_order_id"})

        except Exception as e:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"INTERNAL_ERROR: {str(e)}"})
            raise

    def _reconcile_ambiguous_payment(self):
        """
        Deterministic reconciliation loop.
        Never duplicates an order if the original intent succeeded remotely despite dropping the response.
        """
        self._transition_and_trigger(CommerceState.RECONCILIATION_REQUIRED)
        
        try:
            orders = self.payment_adapter.service.fetch_orders_by_receipt(self.receipt_id)
            if orders and len(orders) > 0:
                # We found the order! The server processed it before dropping connection.
                # Do NOT create a new order. Link the existing one.
                self._transition_and_trigger(CommerceState.RECOVERED_SUCCESS, {"recovered_order_id": orders[0]["id"]})
                self._transition_and_trigger(CommerceState.COMPLETED)
            else:
                # The server truly never processed it.
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "REMOTE_ORDER_NOT_FOUND_AFTER_TIMEOUT"})
        except Exception as e:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"RECONCILIATION_FAILED: {str(e)}"})

    def _execute_payment_validation(self):
        """Strictly revalidates inventory, price, and shipping immediately before payment."""
        total_price = 0
        
        for item in self.cart:
            sku = item.sku
            
            # 1. Re-validate Inventory
            stock = self.inventory_db.get(sku, 0)
            if stock <= 0:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "STALE_INVENTORY", "sku": sku})
                return
                
            # 2. Re-validate Price
            canonical_price = self.pricing_db.get(sku)
            if canonical_price is None or getattr(item, 'price_paise', 0) != canonical_price:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "STALE_PRICE", "sku": sku})
                return
                
            total_price += canonical_price
            
        # 3. Re-validate Shipping / Merchant Policy Check
        if not self.merchant_policy_db.get("shipping_available", True):
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "STALE_SHIPPING_POLICY"})
            return
            
        self.final_total_paise = total_price + self.merchant_policy_db.get("flat_shipping_paise", 0)

    def _execute_prechecks(self):
        total_price = 0
        
        for item in self.cart:
            sku = item.sku
            
            # 1. Inventory Check
            stock = self.inventory_db.get(sku, 0)
            if stock <= 0:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "INVENTORY_ZERO", "sku": sku})
                return
                
            # 2. Price Check (compare agent's known price vs canonical DB price)
            canonical_price = self.pricing_db.get(sku)
            if canonical_price is None or getattr(item, 'price_paise', 0) != canonical_price:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "PRICE_MISMATCH", "sku": sku})
                return
                
            total_price += canonical_price
            
        # 3. Shipping / Merchant Policy Check
        if not self.merchant_policy_db.get("shipping_available", True):
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "SHIPPING_UNAVAILABLE"})
            return
            
        # 4. Final total calculation (add shipping flat fee if any)
        shipping_fee = self.merchant_policy_db.get("flat_shipping_paise", 0)
        self.final_total_paise = total_price + shipping_fee
