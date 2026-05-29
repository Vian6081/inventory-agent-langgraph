import sqlite3
from langchain_core.tools import tool

# The database file created by db_setup.py
DB_PATH = "inventory.db"

# 1. READ TOOLS

@tool
def check_stock(sku: str) -> dict:
    """
    # Fetches the current stock level and details for a single specific SKU. Use this only when the user provides an exact SKU.
    """
    
    clean_sku = sku.strip().upper()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, category, warehouse, stock_level FROM items WHERE sku = ?", (clean_sku,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        data = {"name": row[0], "category": row[1], "warehouse": row[2], "stock_level": row[3]}
        return {"status": "success", "sku": clean_sku, "data": data}
    else:
        return {"status": "error", "message": f"SKU '{clean_sku}' not found in database. Ask user to verify."}


@tool
def list_items(category: str = None, warehouse: str = None) -> dict:
    """
    Returns a list of items filtered by category or warehouse. 
    Use this when the user asks for general items (e.g., 'show me all electronics' or 'what is in Gurgaon').
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    
    if category:
        query += " AND LOWER(category) = ?"
        params.append(category.strip().lower())
        
    if warehouse:
        query += " AND LOWER(warehouse) = ?"
        params.append(warehouse.strip().lower())
        
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if rows:
        return {"status": "success", "count": len(rows), "items": rows}
    else:
        return {"status": "empty", "message": "No items matched those filters."}


# 2. SUMMARISE TOOL (The Boss Level)

@tool
def summarise_inventory(scope: str) -> dict:
    """
    Generates a high-level statistical overview of the inventory.
    Valid scopes are strictly: 'by_warehouse', 'by_category', or 'total'.
    Use this when the user asks for summaries, totals, or broad overviews.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    clean_scope = scope.strip().lower()
    digest = {}
    
    if clean_scope == "by_warehouse":
        cursor.execute("SELECT warehouse, SUM(stock_level) FROM items GROUP BY warehouse")
        for row in cursor.fetchall():
            digest[row[0]] = row[1]
            
    elif clean_scope == "by_category":
        cursor.execute("SELECT category, SUM(stock_level) FROM items GROUP BY category")
        for row in cursor.fetchall():
            digest[row[0]] = row[1]
            
    elif clean_scope == "total":
        cursor.execute("SELECT SUM(stock_level) FROM items")
        row = cursor.fetchone()
        digest["total_stock"] = row[0] if row[0] else 0
        
    else:
        conn.close()
        return {
            "status": "error", 
            "message": f"Invalid scope '{scope}'. You must use 'by_warehouse', 'by_category', or 'total'."
        }
        
    conn.close()
    return {"status": "success", "scope": clean_scope, "digest": digest}


# 3. WRITE & DELETE TOOLS

@tool
def update_stock(sku: str, delta: int) -> dict:
    """
    Adjusts inventory count. 
    Pass a positive delta to add stock, or a negative delta to remove stock.
    """
    clean_sku = sku.strip().upper()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if SKU exists first
    cursor.execute("SELECT stock_level FROM items WHERE sku = ?", (clean_sku,))
    if not cursor.fetchone():
        conn.close()
        return {"status": "error", "message": f"Cannot update. SKU '{clean_sku}' not found."}
        
    # Apply the update
    cursor.execute("UPDATE items SET stock_level = stock_level + ? WHERE sku = ?", (delta, clean_sku))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"Stock for {clean_sku} adjusted by {delta}."}


@tool
def delete_item(sku: str) -> dict:
    """
    Deletes an item record entirely from the database.
    Use only when the user explicitly requests to delete or remove a SKU.
    """
    clean_sku = sku.strip().upper()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM items WHERE sku = ?", (clean_sku,))
    changes = conn.total_changes
    conn.commit()
    conn.close()
    
    if changes > 0:
        return {"status": "success", "message": f"SKU '{clean_sku}' deleted successfully."}
    else:
        return {"status": "error", "message": f"Cannot delete. SKU '{clean_sku}' not found."}


# 4. LOCAL TESTING BLOCK
if __name__ == "__main__":
    print("Testing tools directly against inventory.db...\n")
    print("1. Check Stock:", check_stock.invoke({"sku": "LAPTOP-01"}))
    print("2. Summarise by Warehouse:", summarise_inventory.invoke({"scope": "by_warehouse"}))