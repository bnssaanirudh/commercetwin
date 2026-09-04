import os
import csv
import sys

def validate():
    catalog_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'merchant', 'catalog.csv')
    
    if not os.path.exists(catalog_path):
        print("FAIL: catalog.csv not found")
        sys.exit(1)
        
    skus = set()
    errors = []
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        reader = list(csv.DictReader(f))
        
        if len(reader) < 120 or len(reader) > 150:
            errors.append(f"Row count {len(reader)} out of bounds [120-150]")
            
        for idx, row in enumerate(reader):
            # Check SKU uniqueness
            sku = row.get('sku')
            if not sku:
                errors.append(f"Row {idx}: missing SKU")
                continue
            if sku in skus:
                errors.append(f"Row {idx}: duplicate SKU {sku}")
            skus.add(sku)
            
            # Check financials
            try:
                price = int(row['price_paise'])
                cost = int(row['cost_paise'])
                if price <= 0 or cost <= 0:
                    errors.append(f"SKU {sku}: Non-positive price or cost")
                if price < cost:
                    errors.append(f"SKU {sku}: Price less than cost")
            except ValueError:
                errors.append(f"SKU {sku}: Invalid price/cost format")
                
            # Check inventory
            try:
                inv = int(row['inventory'])
                if inv < 0:
                    errors.append(f"SKU {sku}: Negative inventory")
            except ValueError:
                errors.append(f"SKU {sku}: Invalid inventory format")

    if errors:
        print("FAIL: Validation errors found")
        for err in errors:
            print(" -", err)
        sys.exit(1)
        
    print("PASS")

if __name__ == "__main__":
    validate()
