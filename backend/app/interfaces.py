from typing import Protocol, Any, Dict, List

class ModelAdapter(Protocol):
    """Protocol for LLM interactions, isolating reasoning from core logic."""
    async def generate_structured(self, prompt: str, schema: Any) -> Any: ...

class MerchantTwinRepository(Protocol):
    """Protocol for reading merchant twin state (catalog, inventory, pricing)."""
    async def get_product(self, sku: str) -> Any: ...
    async def verify_inventory(self, sku: str, quantity: int) -> bool: ...

class BuyerAgent(Protocol):
    """Protocol for AI-driven buyer personas exploring the twin."""
    async def act(self, state: Dict[str, Any]) -> Any: ...

class ChaosInjector(Protocol):
    """Protocol for perturbing the twin state or transactions deterministically."""
    async def inject(self, target: str, context: Dict[str, Any]) -> None: ...

class TraceRecorder(Protocol):
    """Protocol for recording immutable event traces during experiments."""
    async def record_event(self, trace_id: str, event_type: str, payload: Dict[str, Any]) -> None: ...

class FailureLocalizer(Protocol):
    """Protocol for analyzing traces to categorize failures and revenue leaks."""
    async def analyze(self, trace_id: str) -> Any: ...

class RepairSynthesizer(Protocol):
    """Protocol for proposing fixes to localized failures."""
    async def synthesize(self, failure_context: Any) -> Any: ...

class PaymentAdapter(Protocol):
    """Protocol for Test Mode Razorpay integrations, restricted by least privilege."""
    async def create_order(self, amount_paise: int, currency: str, receipt: str) -> Dict[str, Any]: ...
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool: ...
