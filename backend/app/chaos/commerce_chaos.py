import random
from typing import List, Dict, Any
from app.models import Product
from app.chaos.engine import ChaosInjection

def apply_commerce_chaos(products: List[Product], inventory: Dict[str, int], 
                         pricing: Dict[str, int], policy: Dict[str, Any], seed: int) -> List[ChaosInjection]:
    random.seed(seed + 2)
    injections = []
    
    if not products:
        return injections
        
    skus = [p.sku for p in products]
    
    # 1. INVENTORY: Sells out after discovery
    target_inv = random.choice(skus)
    before_inv = inventory.get(target_inv, 0)
    if before_inv > 0:
        inj = ChaosInjection(
            chaos_id=f"INV_ZERO_{target_inv}",
            family="inventory",
            target=target_inv,
            severity="high",
            seed=seed,
            before_state={"stock": before_inv},
            mutated_state={"stock": 0},
            reversible_patch={"sku": target_inv, "stock": before_inv},
            start_boundary="READY_FOR_PAYMENT", # Happens right before payment
            end_boundary="COMPLETED"
        )
        injections.append(inj)

    # 2. PRICE: Price changes after selection
    target_price = random.choice(skus)
    before_price = pricing.get(target_price, 1000)
    new_price = int(before_price * 1.5)
    inj = ChaosInjection(
        chaos_id=f"PRICE_HIKE_{target_price}",
        family="price",
        target=target_price,
        severity="medium",
        seed=seed,
        before_state={"price_paise": before_price},
        mutated_state={"price_paise": new_price},
        reversible_patch={"sku": target_price, "price_paise": before_price},
        start_boundary="READY_FOR_PAYMENT", 
        end_boundary="COMPLETED"
    )
    injections.append(inj)
    
    # 3. CHECKOUT: Shipping unavailable
    before_shipping = policy.get("shipping_available", True)
    inj = ChaosInjection(
        chaos_id="CHK_NOSHIP",
        family="checkout",
        target="merchant_policy",
        severity="high",
        seed=seed,
        before_state={"shipping_available": before_shipping},
        mutated_state={"shipping_available": False},
        reversible_patch={"key": "shipping_available", "value": before_shipping},
        start_boundary="READY_FOR_PAYMENT",
        end_boundary="COMPLETED"
    )
    injections.append(inj)

    # 4. CATALOG: Missing Typed Attribute
    target_attr_sku = random.choice(skus)
    inj = ChaosInjection(
        chaos_id=f"DROP_ATTR_{target_attr_sku}",
        family="catalog",
        target=target_attr_sku,
        severity="medium",
        seed=seed,
        before_state={"has_attribute": True},
        mutated_state={"has_attribute": False},
        reversible_patch={"sku": target_attr_sku, "action": "restore_attribute"},
        start_boundary="READY_FOR_PAYMENT",
        end_boundary="COMPLETED"
    )
    injections.append(inj)
    
    # We don't apply these instantly in the engine initialization for commerce chaos;
    # they are scheduled and triggered dynamically by boundaries. 
    return injections
