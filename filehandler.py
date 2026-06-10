import pandas as pd
import sqlite3
import os

DB_PATH = "inventory.db"

def ingest_mavenir_cmdb(file_path: str):
    """Reads the Mavenir CMDB Excel file, transforms it, and loads it into SQLite."""
    print(f"\n[EXCEL] Processing Mavenir CMDB Data from {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    # 1. Read ONLY the raw data sheet, ignoring the summary sheet
    try:
        # Assuming the main data is on a sheet named 'CMDB' based on your filename
        # If it's a CSV, use pd.read_csv(file_path) instead
        df = pd.read_csv(file_path) 
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # 2. Data Cleaning
    df.dropna(how='all', inplace=True)
    
    # Standardize column names to lowercase with underscores
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    
    # 3. Map Mavenir's specific CMDB columns to your LangGraph schema
    rename_map = {
        "serial_no": "sku",
        "display_name": "name",
        "category": "category",
        "location": "warehouse"
    }
    df.rename(columns=rename_map, inplace=True)
    
    # 4. The Magic Trick: Add a stock level of 1 for every individual server
    df['stock_level'] = 1
    
    # 5. Filter down to ONLY the columns your SQLite database expects
    # (We drop things like IP Address, OS, etc., to keep the DB clean)
    columns_to_keep = ['sku', 'name', 'category', 'warehouse', 'stock_level']
    
    # Handle any missing columns just in case
    for col in columns_to_keep:
        if col not in df.columns:
            df[col] = "unknown"
            
    final_df = df[columns_to_keep].copy()

    # 6. Enforce string casing for LangGraph matching
    final_df['sku'] = final_df['sku'].astype(str).str.strip().str.upper()
    final_df['warehouse'] = final_df['warehouse'].astype(str).str.strip().str.lower()
    final_df['category'] = final_df['category'].astype(str).str.strip().str.lower()

    # 7. Load to SQLite
    conn = sqlite3.connect(DB_PATH)
    # Using 'replace' here so if you run this twice, it overwrites the old DB
    # instead of duplicating all the servers.
    final_df.to_sql("items", conn, if_exists="replace", index=False)
    conn.close()
    
    print(f"Successfully ingested {len(final_df)} servers into inventory.db!")

if __name__ == "__main__":
    # Test it with your exact file name!
    # Update this path if the CSV is in a different folder
    ingest_mavenir_cmdb("CMDB test data.xlsx - CMDB.csv")