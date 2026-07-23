"""
AI Copilot UI Component

Provides an interactive chat interface embedded directly into dashboards.
Sends conversation history and user prompts to POST /copilot/chat.
"""

import streamlit as st
from api_client import APIClient


def render_copilot():
    st.subheader("🤖 RealtyCRM AI Copilot")
    st.caption("Ask questions, manage leads, or filter properties using natural language.")

    # Initialize chat history in session state
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []

    # Display prior conversation messages
    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Accept user prompt
    if user_prompt := st.chat_input("Type your message here..."):
        # Append user message
        st.session_state.copilot_messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Format history for backend payload schema
        formatted_history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.copilot_messages[:-1]
        ]

        payload = {
            "message": user_prompt,
            "history": formatted_history
        }

        with st.spinner("AI Copilot is thinking..."):
            res = APIClient.post("/copilot/chat", data=payload)

        if "error" in res:
            assistant_reply = f"⚠️ Error: {res['error']}"
        else:
            assistant_reply = res.get("response", "No response received.")

        # Append and display assistant response
        st.session_state.copilot_messages.append({"role": "assistant", "content": assistant_reply})
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)