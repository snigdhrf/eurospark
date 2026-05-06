import streamlit as st
import httpx
import base64
from PIL import Image
import io
import os

# Backend URL (set this in Render env vars)
BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "https://eurospark-docker-v0.onrender.com"
)

st.set_page_config(
    page_title="EuroSpark ⚡",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ EuroSpark — European Energy Analytics")
st.caption(
    "Ask natural language questions about EU electricity prices, renewables, and consumption."
)

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart"):
            img = Image.open(io.BytesIO(base64.b64decode(msg["chart"])))
            st.image(img, use_column_width=True)

# User input
if prompt := st.chat_input(
    "e.g. Which country had the highest renewable share in 2022?"
):
    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Call backend
    with st.chat_message("assistant"):
        placeholder = st.empty()

        try:
            response = httpx.post(
                f"{BACKEND_URL}/run",
                json={
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                },
                timeout=60
            )

            data = response.json()

            # Extract response safely
            messages = data.get("messages", [])

            if not messages:
                raise ValueError("No messages returned from backend")

            last_msg = messages[-1]

            full_text = last_msg.get("content", "No response generated.")
            chart_b64 = last_msg.get("chart", None)

        except Exception as e:
            full_text = f"⚠️ Error: {str(e)}"
            chart_b64 = None

        # Display text
        placeholder.markdown(full_text)

        # Display chart if exists
        if chart_b64:
            img = Image.open(io.BytesIO(base64.b64decode(chart_b64)))
            st.image(img, use_column_width=True)

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text,
        "chart": chart_b64
    })