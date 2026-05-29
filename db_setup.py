import sqlite3

conn = sqlite3.connect("inventory.db")
cursor = conn.cursor()

cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS items (
        sku TEXT PRIMARY KEY,
        name TEXT,
        category TEXT,
        warehouse TEXT,
        stock_level INTEGER
    )
    '''

)
conn.commit()
conn.close()
print("✅ Database built! 'inventory.db' is locked and loaded.")