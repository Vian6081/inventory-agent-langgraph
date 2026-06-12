import streamlit as st
import sqlite3
import pandas as pd
from graph import ask_inventory_agent

# Changed from "wide" to "centered" for a much cleaner, ChatGPT-style look
st.set_page_config(page_title="Mavenir AI Inventory Agent", layout="centered")

DB_PATH = "inventory.db"

# ==========================================
# MAIN CHAT UI
# ==========================================
st.title("Mavenir AI Inventory Agent")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# THE HIDDEN ADMIN MENU (Popover UI)
# ==========================================
# Everything is tucked neatly inside this single button above the chat bar
with st.popover("⚙️ Database & Upload"):
    st.markdown("**Upload CMDB Data**")
    uploaded_file = st.file_uploader("Choose an Excel file (.xlsx)", type=["xlsx"], label_visibility="collapsed")
    
    replace_mode = st.radio("Import mode", ["Replace all existing data", "Add to existing data"], index=0)

    if uploaded_file is not None:
        if st.button("📥 Import File", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    df = pd.read_excel(uploaded_file, sheet_name="CMDB")
                    df.dropna(how='all', inplace=True)
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()

                    if replace_mode == "Replace all existing data":
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
                            str(row.get("Serial No")).strip().upper(),
                            str(row.get("Display Name")),
                            str(row.get("Category")).strip().lower(),
                            str(row.get("Location")).strip().lower(),
                            1
                        ))

                    if replace_mode == "Replace all existing data":
                        cursor.executemany("""
                            INSERT INTO items (sku, name, category, warehouse, stock_level) 
                            VALUES (?, ?, ?, ?, ?)
                        """, rows)
                    else:
                        cursor.executemany("""
                            INSERT OR IGNORE INTO items (sku, name, category, warehouse, stock_level) 
                            VALUES (?, ?, ?, ?, ?)
                        """, rows)

                    conn.commit()
                    conn.close()
                    st.success(f"✅ {len(rows)} records imported successfully!")
                except Exception as e:
                    st.error(f"Error importing file: {str(e)}")
    
    st.divider()
    
    # Teammate's metrics, safely hidden from the main UI
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        conn.close()
        st.metric("📊 Total records in database", count)
    except:
        st.warning("No database found yet.")

    if st.button("🗑️ Clear all data", use_container_width=True):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items")
            conn.commit()
            conn.close()
            st.success("All data cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ==========================================
# CHAT INPUT BAR
# ==========================================
if prompt := st.chat_input("Ask me about your inventory..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call your LangGraph Agent!
                response = ask_inventory_agent(st.session_state.messages)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")