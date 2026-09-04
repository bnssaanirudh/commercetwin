import os
import csv
import json
import random
import uuid
import sys
from typing import List, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.buyers.schemas import BuyerIntentSchema, HardConstraints, SoftPreferences
from app.buyers.oracle import IntentOracle

# Mock models so we don't need a DB connection just to evaluate
class MockProduct:
    def __init__(self, sku: str, category: str, price_paise: int):
        self.sku = sku
        self.category = category
        self.price_paise = price_paise

class MockAttribute:
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

def load_catalog():
    catalog_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'merchant', 'catalog.csv')
    products = []
    attributes_map = {}
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['sku']
            prod = MockProduct(sku, row['category'], int(row['price_paise']))
            products.append(prod)
            
            attrs = []
            for key in ['connector', 'wattage', 'usb_pd', 'os_support', 'port_count', 'resolution', 'wireless', 'bluetooth', 'battery', 'dimensions', 'variant', 'shipping_class']:
                val = row.get(key)
                if val and str(val).strip() != "":
                    attrs.append(MockAttribute(key, str(val)))
            attributes_map[sku] = attrs
            
    return products, attributes_map

def find_valid_solutions(intent: BuyerIntentSchema, products: List[MockProduct], attrs_map: Dict[str, List[MockAttribute]]) -> List[List[MockProduct]]:
    oracle = IntentOracle(intent)
    valid_single_skus = []
    
    # Simple check for single-product intents
    if len(intent.hard_constraints.required_categories) == 1:
        for p in products:
            sku_res = oracle.evaluate_sku(p, attrs_map[p.sku])
            if sku_res.is_valid:
                cart_res = oracle.evaluate_cart([p], p.price_paise)
                if cart_res.is_valid:
                    valid_single_skus.append([p])
        return valid_single_skus
        
    # For multiple required categories (e.g. bundles of 2), we do a simple N^2 check
    valid_bundles = []
    if len(intent.hard_constraints.required_categories) == 2:
        cat1 = intent.hard_constraints.required_categories[0]
        cat2 = intent.hard_constraints.required_categories[1]
        
        prods1 = [p for p in products if p.category == cat1]
        prods2 = [p for p in products if p.category == cat2]
        
        for p1 in prods1:
            sku1_res = oracle.evaluate_sku(p1, attrs_map[p1.sku])
            if not sku1_res.is_valid:
                continue
            for p2 in prods2:
                sku2_res = oracle.evaluate_sku(p2, attrs_map[p2.sku])
                if not sku2_res.is_valid:
                    continue
                
                cart_res = oracle.evaluate_cart([p1, p2], p1.price_paise + p2.price_paise)
                if cart_res.is_valid:
                    valid_bundles.append([p1, p2])
                    
    return valid_bundles

def generate_intent(difficulty: int, all_categories: List[str], products: List[MockProduct], attrs_map: Dict[str, List[MockAttribute]]) -> BuyerIntentSchema:
    while True: # Loop until we generate a valid one (unless impossible)
        req_cats = random.sample(all_categories, 1 if difficulty in [1,2,3,5,6] else 2)
        forb_cats = random.sample([c for c in all_categories if c not in req_cats], random.randint(0, 2)) if difficulty >= 2 else []
        
        target_budget = random.randint(100000, 1000000) # 1k to 10k INR
        max_budget = int(target_budget * random.uniform(1.1, 1.3))
        
        min_attrs = {}
        comp_attrs = {}
        if difficulty >= 3:
            if "usb_c_chargers" in req_cats:
                min_attrs["wattage"] = float(random.choice([20, 65, 100]))
            if "cables" in req_cats:
                comp_attrs["connector"] = random.choice(["USB-C", "Lightning"])
                
        is_impossible = (random.random() < 0.05)
        
        req_str = " and a ".join([c.replace('_', ' ') for c in req_cats])
        forb_str = " or ".join([c.replace('_', ' ') for c in forb_cats]) if forb_cats else ""
        
        templates = [
            f"I want to purchase a {req_str} for under {max_budget/100} rupees.",
            f"Looking for a {req_str}." + (f" Please do not include any {forb_str}." if forb_str else ""),
            f"Need to buy a {req_str}. Budget is strictly {max_budget/100} INR.",
            f"Can you find me a {req_str}?" + (f" I hate {forb_str}." if forb_str else f" Any good options under {max_budget/100}?"),
            f"Procure a {req_str} for me." + (f" Exclude {forb_str}." if forb_str else ""),
            f"Shopping for a {req_str}. Max I can spend is {max_budget/100}.",
            f"I'm in the market for a {req_str}." + (f" Definitely no {forb_str}." if forb_str else ""),
            f"Need a {req_str}. Budget: {max_budget/100}. " + (f"Avoid {forb_str}." if forb_str else ""),
            f"Get me a {req_str}. " + (f"No {forb_str} please!" if forb_str else ""),
            f"Searching for a {req_str}."
        ]
        
        raw_intent = random.choice(templates) + (" Make it impossible." if is_impossible else "")
        raw_intent += f" {uuid.uuid4().hex[:6]}" # Ensure strict uniqueness just in case
        
        intent = BuyerIntentSchema(
            intent_id=f"INT-{uuid.uuid4().hex[:8]}",
            raw_intent=raw_intent,
            hard_constraints=HardConstraints(
                required_categories=req_cats,
                forbidden_categories=forb_cats,
                min_attributes=min_attrs,
                compatibility=comp_attrs
            ),
            soft_preferences=SoftPreferences(preferred_attributes={"color": "black"}),
            target_budget_paise=target_budget,
            max_budget_paise=max_budget,
            autonomy_level="autonomous" if difficulty == 6 else "supervised",
            seed=random.randint(0, 99999)
        )
        
        sols = find_valid_solutions(intent, products, attrs_map)
        
        if is_impossible and len(sols) == 0:
            return intent
        elif not is_impossible and len(sols) > 0:
            intent.oracle_valid_product_conditions = {"num_solutions": len(sols)}
            return intent
        # Otherwise, try again

def main():
    random.seed(42) # Deterministic
    
    products, attrs_map = load_catalog()
    categories = list(set([p.category for p in products]))
    
    scenarios = []
    
    # 500 total: 300 dev, 100 val, 100 held_out
    for i in range(500):
        # Evenly distribute difficulty 1-6
        difficulty = (i % 6) + 1
        intent = generate_intent(difficulty, categories, products, attrs_map)
        
        split = "dev"
        if i >= 400:
            split = "held_out"
        elif i >= 300:
            split = "val"
            
        scenarios.append({
            "split": split,
            "difficulty": difficulty,
            "intent": intent.model_dump()
        })
        
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'data', 'scenarios'), exist_ok=True)
    
    for split_name in ["dev", "val", "held_out"]:
        filepath = os.path.join(os.path.dirname(__file__), '..', 'data', 'scenarios', f"{split_name}.jsonl")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if split_name == "held_out":
                f.write("# WARNING: FROZEN DATASET. Do not use for training or prompt tuning.\n")
                
            split_scenarios = [s for s in scenarios if s["split"] == split_name]
            for s in split_scenarios:
                f.write(json.dumps(s) + "\n")
                
    print(f"Generated 500 scenarios across dev/val/held_out")

if __name__ == "__main__":
    main()
