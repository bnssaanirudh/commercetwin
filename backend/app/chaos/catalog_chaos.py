import random

from app.chaos.engine import ChaosInjection
from app.models import Product


def apply_catalog_chaos(products: list[Product], seed: int) -> list[ChaosInjection]:
    random.seed(seed + 1) # offset seed for different rng sequence
    injections = []

    mutations = [
        "ambiguous_units",
        "stale_descriptive_text",
        "missing_category_mapping"
    ]

    # Apply about 20 mutations
    num_mutations = min(20, len(products))
    targets = random.sample(range(len(products)), num_mutations)

    for idx in targets:
        p = products[idx]
        mutation = random.choice(mutations)

        if mutation == "ambiguous_units":
            before_title = p.title
            # Attempt to strip common units
            new_title = before_title.replace("140W", "140").replace("65W", "65").replace("100W", "100")
            if new_title == before_title:
                new_title = before_title + " (ambiguous)"
            p.title = new_title

            inj = ChaosInjection(
                chaos_id=f"CAT_UNITS_{p.sku}",
                family="catalog",
                target=p.sku,
                severity="medium",
                seed=seed,
                before_state={"title": before_title},
                mutated_state={"title": new_title},
                reversible_patch={"index": idx, "field": "title", "value": before_title},
                start_boundary="DISCOVERY",
                end_boundary="EVALUATION"
            )
            injections.append(inj)

        elif mutation == "stale_descriptive_text":
            before_desc = p.description
            p.description = "Outdated description. Please refer to external manual."

            inj = ChaosInjection(
                chaos_id=f"CAT_STALE_{p.sku}",
                family="catalog",
                target=p.sku,
                severity="low",
                seed=seed,
                before_state={"description": before_desc},
                mutated_state={"description": p.description},
                reversible_patch={"index": idx, "field": "description", "value": before_desc},
                start_boundary="DISCOVERY",
                end_boundary="EVALUATION"
            )
            injections.append(inj)

        elif mutation == "missing_category_mapping":
            before_cat = p.category
            p.category = "unknown"

            inj = ChaosInjection(
                chaos_id=f"CAT_NOCAT_{p.sku}",
                family="catalog",
                target=p.sku,
                severity="high",
                seed=seed,
                before_state={"category": before_cat},
                mutated_state={"category": "unknown"},
                reversible_patch={"index": idx, "field": "category", "value": before_cat},
                start_boundary="DISCOVERY",
                end_boundary="EVALUATION"
            )
            injections.append(inj)

    return injections
