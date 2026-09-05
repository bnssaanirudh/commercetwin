from typing import Any

import requests

from app.buyers.agent import BaseBuyerAgent
from app.models import Product

from .state import CommerceState, CommerceStateMachine


class CommerceRunnerError(Exception):
    pass


class CommerceRunner:
    def __init__(
        self,
        agent: BaseBuyerAgent,
        inventory_db: dict[str, int],
        pricing_db: dict[str, int],
        merchant_policy_db: dict[str, Any],
        chaos_engine=None,
        payment_adapter=None,
        trace_id: str | None = None,
    ) -> None:
        import uuid
        self.trace_id = trace_id or f"TR-{uuid.uuid4().hex[:8]}"
        self.agent = agent
        self.state_machine = CommerceStateMachine(self.trace_id)

        # In-process DB snapshots for deterministic precheck
        self.inventory_db = inventory_db
        self.pricing_db = pricing_db
        self.merchant_policy_db = merchant_policy_db
        self.chaos_engine = chaos_engine
        self.payment_adapter = payment_adapter

        self.cart: list[Product] = []
        self.final_total_paise: int = 0
        self.receipt_id: str | None = None

    def _transition_and_trigger(self, state: CommerceState, data: dict | None = None) -> None:
        self.state_machine.transition_to(state, data)
        if self.chaos_engine:
            self.chaos_engine.trigger_boundary(state.name)

    def run_to_precheck(self) -> None:
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

        except CommerceRunnerError:
            raise
        except (ValueError, KeyError, AttributeError) as e:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"UNEXPECTED_ERROR: {e!s}"})
            raise CommerceRunnerError(str(e)) from e

    def process_payment(self, receipt_id: str = "receipt_default") -> None:
        """Final checkout validation strictly blocking stale context."""
        if self.state_machine.current_state != CommerceState.READY_FOR_PAYMENT:
            return

        self.receipt_id = receipt_id

        try:
            self._transition_and_trigger(CommerceState.PAYMENT)
            self._execute_payment_validation()

            if self.state_machine.current_state != CommerceState.ABORTED:
                if self.payment_adapter:
                    try:
                        # Attempt to create remote order
                        order = self.payment_adapter.create_order(
                            amount_paise=self.final_total_paise,
                            receipt=self.receipt_id,
                        )
                        self._transition_and_trigger(CommerceState.PAYMENT_PENDING, {"order_id": order["id"]})
                        return
                    except requests.exceptions.ReadTimeout:
                        # Network dropout. State is ambiguous.
                        self._transition_and_trigger(CommerceState.AMBIGUOUS_REMOTE_STATE)
                        self._reconcile_ambiguous_payment()
                        return
                    except (requests.exceptions.RequestException, OSError, ValueError) as e:
                        # Direct failure (e.g., 5xx, or other known hard fails)
                        self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"PAYMENT_ERROR: {e!s}"})
                        return

                # No adapter — simulation mode goes directly to PAYMENT_PENDING
                self._transition_and_trigger(CommerceState.PAYMENT_PENDING, {"order_id": "mock_order_id"})

        except CommerceRunnerError:
            raise
        except (ValueError, KeyError, AttributeError) as e:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"INTERNAL_ERROR: {e!s}"})
            raise CommerceRunnerError(str(e)) from e

    def _reconcile_ambiguous_payment(self) -> None:
        """
        Deterministic reconciliation loop.
        Never duplicates an order if the original intent succeeded remotely
        despite the connection being dropped before we got the response.
        """
        self._transition_and_trigger(CommerceState.RECONCILIATION_REQUIRED)

        try:
            if self.payment_adapter is None or not hasattr(self.payment_adapter, "service"):
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "NO_PAYMENT_ADAPTER"})
                return

            orders = self.payment_adapter.service.fetch_orders_by_receipt(self.receipt_id)

            valid_orders = []
            for o in orders:
                if (
                    o.get("amount") == self.final_total_paise
                    and o.get("currency") == "INR"
                    and o.get("status") in ("created", "paid", "attempted")
                ):
                    valid_orders.append(o)

            if valid_orders:
                # Found a matching order — server processed it, link existing one.
                self._transition_and_trigger(CommerceState.RECOVERED_SUCCESS, {"recovered_order_id": valid_orders[0]["id"]})
                self._transition_and_trigger(CommerceState.COMPLETED)
            else:
                # Server truly never processed it or no matching order exists.
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "REMOTE_ORDER_NOT_FOUND_AFTER_TIMEOUT"})
        except (OSError, ValueError, KeyError) as e:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": f"RECONCILIATION_FAILED: {e!s}"})

    def _execute_payment_validation(self) -> None:
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
            if canonical_price is None or getattr(item, "price_paise", 0) != canonical_price:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "STALE_PRICE", "sku": sku})
                return

            total_price += canonical_price

        # 3. Re-validate Shipping / Merchant Policy Check
        if not self.merchant_policy_db.get("shipping_available", True):
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "STALE_SHIPPING_POLICY"})
            return

        self.final_total_paise = total_price + self.merchant_policy_db.get("flat_shipping_paise", 0)

    def _execute_prechecks(self) -> None:
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
            if canonical_price is None or getattr(item, "price_paise", 0) != canonical_price:
                self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "PRICE_MISMATCH", "sku": sku})
                return

            total_price += canonical_price

        # 3. Shipping / Merchant Policy Check
        if not self.merchant_policy_db.get("shipping_available", True):
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "SHIPPING_UNAVAILABLE"})
            return

        # 4. Budget Check: reject if canonical total exceeds buyer's max budget
        intent = self.agent.intent
        max_budget = getattr(intent, "max_budget_paise", None)
        shipping_fee = self.merchant_policy_db.get("flat_shipping_paise", 0)
        provisional_total = total_price + shipping_fee
        if max_budget is not None and provisional_total > max_budget:
            self.state_machine.transition_to(CommerceState.ABORTED, {"reason": "BUDGET_EXCEEDED", "total": provisional_total, "max": max_budget})
            return

        # 5. Final total
        self.final_total_paise = provisional_total
