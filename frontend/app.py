import streamlit as st
import httpx, json, base64
from PIL import Image
import io
import os

LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")

st.set_page_config(page_title="EuroSpark ⚡", page_icon="⚡", layout="wide")
st.title("⚡ EuroSpark — European Energy Analytics")
st.caption("Ask natural language questions about EU electricity prices, renewables, and consumption.")

if "thread_id" not in st.session_state:
    r = httpx.post(f"{LANGGRAPH_URL}/threads", json={})
    st.session_state.thread_id = r.json()["thread_id"]

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart"):
            img = Image.open(io.BytesIO(base64.b64decode(msg["chart"])))
            st.image(img, use_column_width=True)

if prompt := st.chat_input("e.g. Which country had the highest renewable share in 2022?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        chart_b64 = None
        full_text = ""
        
        payload = {
            "thread_id": st.session_state.thread_id,
            "assistant_id": "eurospark",
            "input": {"messages": [{"role": "user", "content": prompt}]},
            "stream_mode": "events",
        }
        
        with httpx.stream("POST", f"{LANGGRAPH_URL}/runs/stream",
                          json=payload, timeout=60) as resp:
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = json.loads(line[5:])
                if data.get("event") == "on_chat_model_stream":
                    chunk = data["data"]["chunk"]["content"]
                    if isinstance(chunk, str):
                        full_text += chunk
                        placeholder.markdown(full_text + "▌")
                if data.get("event") == "on_tool_end":
                    if data["data"]["name"] == "plot_chart":
                        chart_b64 = data["data"]["output"]
        
        placeholder.markdown(full_text)
        if chart_b64:
            img = Image.open(io.BytesIO(base64.b64decode(chart_b64)))
            st.image(img, use_column_width=True)

    st.session_state.messages.append({
        "role": "assistant", "content": full_text, "chart": chart_b64
    })