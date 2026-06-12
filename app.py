import streamlit as st
import sqlite3
import pandas as pd
from graph import ask_inventory_agent

st.set_page_config(page_title="Mavenir AI Inventory Agent", layout="centered")

DB_PATH = "inventory.db"

# ==========================================
# 🧠 THE REPOSITORY / STRATEGY PATTERN
# Your senior will love this. If they ever want to add JSON, XML, or Parquet,
# you NEVER touch the UI code below. You just add one line to this dictionary!
# ==========================================
FILE_PARSERS = {
    "csv": lambda file: pd.read_csv(file),
    "xlsx": lambda file: pd.read_excel(file, sheet_name="CMDB")
    # Example for the future: "json": lambda file: pd.read_json(file)
}

def ingest_file_to_db(uploaded_file):
    """Handles extracting data regardless of file type and saving to SQLite."""
    # 1. Figure out the file extension (e.g., 'csv' or 'xlsx')
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    # 2. Check if we know how to parse this file
    if file_extension not in FILE_PARSERS:
        raise ValueError(f"Unsupported file format: {file_extension}. Please upload CSV or XLSX.")
    
    # 3. Dynamically read the file using the correct parser
    df = FILE_PARSERS[file_extension](uploaded_file)
    df.dropna(how='all', inplace=True)
    
    # 4. Standard Database Logic (The UI doesn't need to know about this!)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS items")
    cursor.execute("""
        CREATE TABLE items (
            sku TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            warehouse TEXT,
            stock_level INTEGER
        )
    """)

    rows = []
    for _, row in df.iterrows():
        rows.append((
            str(row.get("Serial No", row.get("serial_no"))).strip().upper(),
            str(row.get("Display Name", row.get("display_name"))),
            str(row.get("Category", row.get("category"))).strip().lower(),
            str(row.get("Location", row.get("location"))).strip().lower(),
            1
        ))

    cursor.executemany("""
        INSERT INTO items (sku, name, category, warehouse, stock_level) 
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()
    return len(rows)


# ==========================================
# MAIN CHAT UI
# ==========================================
st.title("Mavenir AI Inventory Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# CHAT INPUT BAR WITH NATIVE ATTACHMENT 📎
# ==========================================
prompt = st.chat_input(
    "Ask me about your inventory...", 
    accept_file=True, 
    file_type=["xlsx", "csv"] 
)

if prompt:
    # 1. Did they attach a file?
    if prompt.files:
        uploaded_file = prompt.files[0]
        
        with st.chat_message("user"):
            st.markdown(f"📎 *Uploaded new CMDB data: `{uploaded_file.name}`*")
            
        with st.status("📥 Importing data into database...", expanded=True) as status:
            try:
                # Look how clean the UI code is now! 
                # It just passes the file to our handler function.
                records_inserted = ingest_file_to_db(uploaded_file)
                status.update(label=f"✅ {records_inserted} records successfully imported!", state="complete", expanded=False)
            except Exception as e:
                status.update(label=f"❌ Error importing data: {str(e)}", state="error", expanded=False)

    # 2. Did they also type a text question?
    if prompt.text:
        st.session_state.messages.append({"role": "user", "content": prompt.text})
        with st.chat_message("user"):
            st.markdown(prompt.text)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = ask_inventory_agent(st.session_state.messages)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {str(e)}")