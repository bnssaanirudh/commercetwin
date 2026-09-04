import csv
import random
import os
import json

CATEGORIES = [
    "usb_c_chargers", "usb_hubs", "laptop_stands", "mice", 
    "keyboards", "webcams", "headphones", "power_banks", 
    "cables", "adapters"
]

def generate_catalog():
    random.seed(42) # Deterministic generation
    products = []
    
    # 1. USB-C Chargers (15 items)
    for i in range(1, 16):
        wattage = random.choice([20, 30, 45, 65, 100, 140])
        cost = wattage * 1000 + random.randint(100, 500)
        price = int(cost * random.uniform(1.2, 1.5))
        sku = f"CHG-USBC-{wattage}W-{i:03d}"
        products.append({
            "sku": sku, "title": f"FastCharge USB-C Adapter {wattage}W (Model {i})",
            "category": "usb_c_chargers", "description": f"A reliable {wattage}W USB-C charger.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "connector": "USB-C", "wattage": wattage, "usb_pd": "Yes" if wattage >= 20 else "No",
            "shipping_class": "standard"
        })

    # 2. USB Hubs (15 items)
    for i in range(1, 16):
        ports = random.choice([4, 6, 8, 10])
        cost = ports * 800 + random.randint(200, 600)
        price = int(cost * random.uniform(1.3, 1.6))
        sku = f"HUB-USBC-{ports}P-{i:03d}"
        products.append({
            "sku": sku, "title": f"MultiPort USB-C Hub {ports}-in-1 (Model {i})",
            "category": "usb_hubs", "description": f"Versatile {ports}-port USB-C hub.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "connector": "USB-C", "port_count": ports, "os_support": "Windows, macOS, Linux",
            "shipping_class": "standard"
        })

    # 3. Laptop Stands (15 items)
    for i in range(1, 16):
        material = random.choice(["Aluminum", "Plastic", "Wood"])
        cost = 1500 if material == "Plastic" else 3000
        price = int(cost * random.uniform(1.4, 1.8))
        sku = f"STD-LAPT-{material[:3].upper()}-{i:03d}"
        products.append({
            "sku": sku, "title": f"Ergonomic {material} Laptop Stand (Model {i})",
            "category": "laptop_stands", "description": f"Sturdy {material.lower()} laptop stand.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "dimensions": f"{random.randint(20,30)}x{random.randint(20,30)}x{random.randint(5,15)} cm",
            "shipping_class": "bulky" if material == "Wood" else "standard"
        })

    # 4. Mice (15 items)
    for i in range(1, 16):
        wireless = random.choice(["Yes", "No"])
        bt = "5.0" if wireless == "Yes" else "N/A"
        cost = 1200 + (1000 if wireless == "Yes" else 0)
        price = int(cost * random.uniform(1.2, 1.7))
        sku = f"MOU-{'WIR' if wireless=='Yes' else 'WRD'}-{i:03d}"
        products.append({
            "sku": sku, "title": f"Precision {'Wireless' if wireless=='Yes' else 'Wired'} Mouse (Model {i})",
            "category": "mice", "description": f"Ergonomic mouse.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "wireless": wireless, "bluetooth": bt,
            "shipping_class": "standard"
        })

    # 5. Keyboards (15 items)
    for i in range(1, 16):
        wireless = random.choice(["Yes", "No"])
        switch = random.choice(["Mechanical", "Membrane"])
        cost = (3000 if switch == "Mechanical" else 1000) + (1000 if wireless == "Yes" else 0)
        price = int(cost * random.uniform(1.2, 1.5))
        sku = f"KBD-{switch[:4].upper()}-{'WIR' if wireless=='Yes' else 'WRD'}-{i:03d}"
        products.append({
            "sku": sku, "title": f"Pro {switch} {'Wireless' if wireless=='Yes' else 'Wired'} Keyboard (Model {i})",
            "category": "keyboards", "description": f"High quality keyboard.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "wireless": wireless, "variant": switch,
            "shipping_class": "standard"
        })

    # 6. Webcams (15 items)
    for i in range(1, 16):
        res = random.choice(["720p", "1080p", "4K"])
        cost = 1500 if res == "720p" else 3000 if res == "1080p" else 8000
        price = int(cost * random.uniform(1.3, 1.6))
        sku = f"CAM-{res}-{i:03d}"
        products.append({
            "sku": sku, "title": f"CrystalClear {res} Webcam (Model {i})",
            "category": "webcams", "description": f"{res} resolution webcam.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "resolution": res, "connector": "USB-A",
            "shipping_class": "standard"
        })

    # 7. Headphones (15 items)
    for i in range(1, 16):
        wireless = random.choice(["Yes", "No"])
        cost = 2000 + (1500 if wireless == "Yes" else 0)
        price = int(cost * random.uniform(1.4, 1.9))
        sku = f"AUD-{'WIR' if wireless=='Yes' else 'WRD'}-{i:03d}"
        products.append({
            "sku": sku, "title": f"Studio {'Wireless' if wireless=='Yes' else 'Wired'} Headphones (Model {i})",
            "category": "headphones", "description": f"Over-ear headphones.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "wireless": wireless, "battery": "20h" if wireless == "Yes" else "N/A",
            "shipping_class": "standard"
        })

    # 8. Power Banks (15 items)
    for i in range(1, 16):
        cap = random.choice([10000, 20000, 26800])
        cost = cap * 10
        price = int(cost * random.uniform(1.2, 1.5))
        sku = f"PWR-BNK-{cap}MAH-{i:03d}"
        products.append({
            "sku": sku, "title": f"HighCap {cap}mAh Power Bank (Model {i})",
            "category": "power_banks", "description": f"Portable power bank.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "battery": f"{cap}mAh", "usb_pd": "Yes",
            "shipping_class": "hazardous" # Lithium batteries often have special shipping
        })

    # 9. Cables (15 items)
    for i in range(1, 16):
        conn = random.choice(["USB-C to USB-C", "USB-A to USB-C", "USB-C to Lightning"])
        cost = 300
        price = int(cost * random.uniform(1.5, 3.0))
        sku = f"CBL-{conn.replace(' ', '').replace('to','2')}-{i:03d}"
        products.append({
            "sku": sku, "title": f"Durable {conn} Cable 1m (Model {i})",
            "category": "cables", "description": f"Braided {conn} cable.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "connector": conn,
            "shipping_class": "standard"
        })

    # 10. Adapters (15 items)
    for i in range(1, 16):
        conn = random.choice(["USB-C to HDMI", "USB-C to Ethernet", "USB-A to USB-C"])
        cost = 800
        price = int(cost * random.uniform(1.3, 1.8))
        sku = f"ADP-{conn.replace(' ', '').replace('to','2')}-{i:03d}"
        products.append({
            "sku": sku, "title": f"Compact {conn} Adapter (Model {i})",
            "category": "adapters", "description": f"Plug and play {conn} adapter.",
            "price_paise": price, "cost_paise": cost, "inventory": random.randint(10, 500),
            "connector": conn,
            "shipping_class": "standard"
        })

    # Ensure uniqueness of SKU (just in case, though logic guarantees it)
    skus = [p["sku"] for p in products]
    assert len(skus) == len(set(skus))

    all_keys = set()
    for p in products:
        all_keys.update(p.keys())
    
    headers = list(all_keys)
    
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data", "merchant"), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "merchant", "catalog.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for p in products:
            writer.writerow(p)

    print(f"Generated {len(products)} products in {out_path}")

if __name__ == "__main__":
    generate_catalog()
