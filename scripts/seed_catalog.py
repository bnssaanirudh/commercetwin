import os
import csv
import json
import sys
from app.db import SessionLocal, engine
from app.models import Base, Merchant, MerchantTwinVersion, Product, ProductAttribute, InventorySnapshot, PricingSnapshot, MerchantPolicy

def seed():
    # Only recreate tables for seeding local sqlite (in production alembic handles it, but for our MVP seed script we can reset)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Create Merchant and Version
    merchant_id = "M_SYNTH_01"
    merchant = Merchant(merchant_id=merchant_id, name="Synthetic Electronics", active_twin_version=1)
    db.add(merchant)
    
    version = MerchantTwinVersion(version_id="v1", merchant_id=merchant_id, version=1, description="Base clean catalog")
    db.add(version)
    
    # 2. Create Policy
    policy_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'merchant', 'merchant_policy.json')
    with open(policy_path, 'r', encoding='utf-8') as f:
        policy_data = json.load(f)
    
    policy = MerchantPolicy(merchant_id=merchant_id, policy_type="core_rules", policy_data=policy_data, version=1)
    db.add(policy)
    
    # 3. Read Catalog and Seed
    catalog_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'merchant', 'catalog.csv')
    with open(catalog_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['sku']
            prod = Product(
                sku=sku,
                merchant_id=merchant_id,
                title=row['title'],
                category=row['category'],
                description=row['description'],
                catalog_version=1
            )
            db.add(prod)
            
            # Attributes
            for key in ['connector', 'wattage', 'usb_pd', 'os_support', 'port_count', 'resolution', 'wireless', 'bluetooth', 'battery', 'dimensions', 'variant', 'shipping_class']:
                val = row.get(key)
                if val and str(val).strip() != "":
                    db.add(ProductAttribute(sku=sku, key=key, value=str(val), type="string"))
            
            # Pricing
            db.add(PricingSnapshot(
                sku=sku, merchant_id=merchant_id,
                price_paise=int(row['price_paise']),
                cost_paise=int(row['cost_paise']),
                currency="INR", version=1
            ))
            
            # Inventory
            db.add(InventorySnapshot(
                sku=sku, merchant_id=merchant_id,
                quantity=int(row['inventory']),
                version=1
            ))

    db.commit()
    print("Database seeded successfully with base catalog.")

if __name__ == "__main__":
    # Allow python -m scripts.seed_catalog from root
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
    seed()
