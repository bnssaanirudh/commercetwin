import json
from typing import List, Dict, Any
from app.buyers.agent import BaseBuyerAgent
from app.buyers.schemas import BuyerIntentSchema
from app.models import Product, ProductAttribute
from app.adapters.llm import BaseModelAdapter, ModelResponse

class LLMBuyer(BaseBuyerAgent):
    def __init__(self, intent: BuyerIntentSchema, products: List[Product], attributes_map: Dict[str, List[ProductAttribute]], adapter: BaseModelAdapter):
        super().__init__(intent, products, attributes_map)
        self.adapter = adapter
        self.total_latency_ms = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.model_calls = 0

    def discover_candidates(self) -> List[Product]:
        # Formulate prompt
        catalog_str = ""
        for p in self.products:
            attrs = self.attributes_map.get(p.sku, [])
            attr_str = ", ".join([f"{a.key}={a.value}" for a in attrs])
            price = getattr(p, 'price_paise', 0) / 100.0
            catalog_str += f"SKU: {p.sku} | Title: {p.title} | Category: {p.category} | Price: {price} | Attrs: {attr_str}\n"

        system_prompt = "You are a shopping assistant. Based on the buyer intent, select the most appropriate SKUs from the catalog. Output ONLY valid JSON containing a list of strings under the key 'proposed_skus'. Example: {\"proposed_skus\": [\"SKU-1\"]}"
        
        prompt = f"Intent: {self.intent.raw_intent}\nBudget max paise: {self.intent.max_budget_paise}\n\nCatalog:\n{catalog_str}"
        
        try:
            response: ModelResponse = self.adapter.generate(prompt=prompt, system_prompt=system_prompt)
            self.total_latency_ms += response.latency_ms
            self.total_prompt_tokens += response.prompt_tokens
            self.total_completion_tokens += response.completion_tokens
            self.model_calls += 1
            
            self.log_trace("MODEL_CALL", {
                "model": "fake_adapter",
                "latency_ms": response.latency_ms,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens
            })

            data = json.loads(response.raw_content)
            proposed_skus = data.get("proposed_skus", [])
        except Exception as e:
            self.log_trace("LLM_ERROR", {"error": str(e)})
            proposed_skus = []

        # Map back to products, preserving order returned by LLM
        sku_to_product = {p.sku: p for p in self.products}
        candidates = []
        for sku in proposed_skus:
            if sku in sku_to_product:
                candidates.append(sku_to_product[sku])
            else:
                self.log_trace("INVALID_ACTION", {"reason": "HALLUCINATED_SKU", "sku": sku})

        return candidates
