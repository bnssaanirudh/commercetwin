from app.buyers.agent import BaseBuyerAgent
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.models import Product

def test_base_buyer_agent():
    intent = BuyerIntentSchema(
        intent_id="test",
        raw_intent="I want a laptop",
        hard_constraints=HardConstraints(required_categories=["electronics"], max_budget_paise=100000),
        soft_preferences=SoftPreferences(),
        target_budget_paise=50000,
        max_budget_paise=100000,
        autonomy_level="autonomous",
        seed=42
    )
    p = Product(sku="TEST", title="Laptop", category="electronics")
    class DummyAgent(BaseBuyerAgent):
        def discover_candidates(self):
            return [p]
        def evaluate_candidates(self, candidates):
            return candidates
        def select_cart(self, valid_candidates):
            return valid_candidates

    agent = DummyAgent(intent, [p], {})
    
    candidates = agent.discover_candidates()
    assert len(candidates) == 1
    
    assert len(agent.trace_events) == 0
