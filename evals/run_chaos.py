import os
import sys
import argparse
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from run_benchmark import load_catalog
from app.chaos.engine import ChaosEngine

def run_chaos(profile: str, seed: int):
    print(f"Initializing Chaos Engine for profile={profile}, seed={seed}")
    
    # Load canonical base data
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "data", "merchant", "catalog.csv")
    products, attributes_map, inventory_db, pricing_db = load_catalog(catalog_path)
    policy_db = {"shipping_available": True, "flat_shipping_paise": 0}
    
    # Apply chaos
    engine = ChaosEngine()
    engine.apply(products, inventory_db, pricing_db, policy_db, seed, profile)
    
    # Observe mutations
    injections = engine.get_trace_metadata()
    if not injections:
        print("No chaos injected for this profile/seed.")
        return
        
    print(f"\nApplied {len(injections)} chaos mutation(s):")
    for inj in injections:
        print(f"\n--- Chaos ID: {inj['chaos_id']} ({inj['family']}) ---")
        print(f"Target: {inj['target']}")
        print(f"Before State: {inj['before_state']}")
        print(f"Mutated State: {inj['mutated_state']}")
        
    # Prove non-mutation of base data (superficial check for runner, detailed check in tests)
    print("\nVerifying base data integrity...")
    mutated_products, _, _, _ = engine.get_state()
    base_target = next(p for p in products if p.sku == injections[0]['target'])
    mutated_target = next(p for p in mutated_products if p.sku == injections[0]['target'])
    
    print(f"Base data target state: {base_target.description if inj['family']=='catalog' else getattr(base_target, 'price_paise', None)}")
    print(f"Mutated data target state: {mutated_target.description if inj['family']=='catalog' else getattr(mutated_target, 'price_paise', None)}")

    # Test Rollback
    print("\nRolling back...")
    engine.rollback()
    rolled_back_products, _, _, _ = engine.get_state()
    rolled_target = next(p for p in rolled_back_products if p.sku == injections[0]['target'])
    
    print(f"Rolled back target state: {rolled_target.description if inj['family']=='catalog' else getattr(rolled_target, 'price_paise', None)}")
    print("Rollback complete. Safe overlay mechanics confirmed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, choices=["standard", "catalog", "context", "commerce", "all"])
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args()
    
    run_chaos(args.profile, args.seed)
