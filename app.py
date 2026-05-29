import streamlit as st
from graph import ask_inventory_agent

st.title("Mavenir AI Inventory Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

text = st.chat_input()

if text:
    with st.chat_message("user"):
        st.write(text)
    st.session_state.messages.append({"role": "user", "content": text})

    response = ask_inventory_agent(st.session_state.messages)

    with st.chat_message("assistant"):
        st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
