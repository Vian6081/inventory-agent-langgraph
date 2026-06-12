import streamlit as st
import sqlite3
import pandas as pd
from graph import ask_inventory_agent

st.set_page_config(page_title="Mavenir AI Inventory Agent", layout="wide")

DB_PATH = "inventory.db"

with st.sidebar:
    st.title("📂 Upload Data")
    st.markdown("Upload an Excel file to add or replace data in the database.")

    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx)",
        type=["xlsx"],
        help="Upload your CMDB Excel sheet here"
    )

    replace_mode = st.radio(
        "Import mode",
        ["Replace all existing data", "Add to existing data"],
        index=0
    )

    if uploaded_file is not None:
        if st.button("📥 Import File", use_container_width=True):
            try:
                df = pd.read_excel(uploaded_file, sheet_name="CMDB")
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()

                if replace_mode == "Replace all existing data":
                    cursor.execute("DROP TABLE IF EXISTS items")
                    cursor.execute("""
                        CREATE TABLE items (
                            sno             INTEGER PRIMARY KEY,
                            display_name    TEXT,
                            ip_address      TEXT,
                            location        TEXT,
                            om_server       TEXT,
                            status          TEXT,
                            isv_partner     TEXT,
                            service_name    TEXT,
                            serial_no       TEXT,
                            hardware_type   TEXT,
                            hardware_make   TEXT,
                            hardware_model  TEXT,
                            monitor_type    TEXT,
                            vertical        TEXT,
                            category        TEXT,
                            server_category TEXT
                        )
                    """)

                rows = []
                for _, row in df.iterrows():
                    rows.append((
                        row.get("S.NO"),
                        row.get("Display Name"),
                        row.get("Ip Address"),
                        row.get("Location"),
                        row.get("Om Server"),
                        row.get("Status"),
                        row.get("Isv Partner"),
                        row.get("Service Name"),
                        row.get("Serial No"),
                        row.get("Hardware Type"),
                        row.get("Hardware Make"),
                        row.get("Hardware Model"),
                        row.get("Monitor Type"),
                        row.get("Vertical"),
                        row.get("Category"),
                        row.get("Server Category"),
                    ))

                if replace_mode == "Replace all existing data":
                    cursor.executemany("""
                        INSERT INTO items (
                            sno, display_name, ip_address, location, om_server, status,
                            isv_partner, service_name, serial_no, hardware_type, hardware_make,
                            hardware_model, monitor_type, vertical, category, server_category
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, rows)
                else:
                    cursor.executemany("""
                        INSERT OR IGNORE INTO items (
                            sno, display_name, ip_address, location, om_server, status,
                            isv_partner, service_name, serial_no, hardware_type, hardware_make,
                            hardware_model, monitor_type, vertical, category, server_category
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, rows)

                conn.commit()
                conn.close()

                st.success(f"✅ {len(rows)} records imported successfully!")
                st.rerun()

            except Exception as e:
                st.error(f" Error importing file: {str(e)}")

    st.divider()

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

st.title("Mavenir AI Inventory Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me about your inventory..."):
 
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = ask_inventory_agent(st.session_state.messages)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f" Error: {str(e)}"
                st.error(error_msg)
