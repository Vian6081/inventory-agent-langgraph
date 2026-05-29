import sqlite3
import random

def seed_massive_database():
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # The building blocks for our fake Mavenir gear
    prefixes = ["5G", "4G", "Edge", "Core", "High-Speed", "Rugged", "Outdoor", "Indoor"]
    item_types = ["Radio Unit", "Fiber Cable", "Server Rack", "Network Switch", "Processor", "Antenna", "Transceiver", "Power Supply"]
    categories = ["Telecom", "Cabling", "Hardware", "Networking", "Power"]
    warehouses = ["Warehouse A", "Warehouse B", "Warehouse C", "Warehouse D", "Warehouse E"]

    # Generate 1000 unique items programmatically
    massive_inventory = []
    for i in range(1, 1001):
        sku = f"SKU-{1000 + i}" # Generates SKU-1001, SKU-1002, etc.
        name = f"{random.choice(prefixes)} {random.choice(item_types)}"
        category = random.choice(categories)
        warehouse = random.choice(warehouses)
        stock_level = random.randint(0, 800) # Random stock between 0 and 800
        
        massive_inventory.append((sku, name, category, warehouse, stock_level))

    # Wipe the old 5 items and inject the 1000 new ones
    cursor.execute('DELETE FROM items')
    
    cursor.executemany('''
        INSERT INTO items (sku, name, category, warehouse, stock_level)
        VALUES (?, ?, ?, ?, ?)
    ''', massive_inventory)

    conn.commit()
    conn.close()
    
    print("🚀 Boom. 1000 Mavenir items successfully injected into inventory.db!")

if __name__ == "__main__":
    seed_massive_database()