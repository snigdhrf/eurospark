import streamlit as st
import httpx
import base64
from PIL import Image
import io
import os

LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:8000")

st.set_page_config(page_title="EuroSpark ⚡", page_icon="⚡", layout="wide")
st.title("⚡ EuroSpark — European Energy Analytics")
st.caption("Ask natural language questions about EU electricity prices, renewables, and consumption.")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart"):
            img = Image.open(io.BytesIO(base64.b64decode(msg["chart"])))
            st.image(img, use_column_width=True)

# User input
if prompt := st.chat_input("e.g. Which country had the highest renewable share in 2022?"):
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = httpx.post(
                f"{LANGGRAPH_URL}/run",
                json={
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=60
            )

            data = response.json()

            # Extract response safely
            output_messages = data.get("messages", [])
            chart_b64 = data.get("chart_base64")

            # Get last assistant message
            if output_messages:
                final_msg = output_messages[-1].get("content", "")
            else:
                final_msg = "No response."

            st.markdown(final_msg)

            # Show chart if exists
            if chart_b64:
                img = Image.open(io.BytesIO(base64.b64decode(chart_b64)))
                st.image(img, use_column_width=True)

    # Save assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_msg,
        "chart": chart_b64
    })