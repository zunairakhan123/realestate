"""
Sidebar Component

Manages user identity display, role badges, and application navigation controls.
"""

import streamlit as st


def render_sidebar(on_logout_callback):
    """
    Renders the navigation sidebar with user session info and logout triggers.
    """
    with st.sidebar:
        st.title("🏢 RealtyCRM Portal")
        st.markdown("---")

        # User Profile Overview
        email = st.session_state.get("user_email", "User")
        role = st.session_state.get("user_role", "unknown").upper()

        st.markdown(f"**Account:** `{email}`")
        
        # Role Badge Display
        if role == "ADMIN":
            st.error(f"🛡️ Role: {role}")
        elif role == "AGENT":
            st.warning(f"👔 Role: {role}")
        else:
            st.info(f"🏡 Role: {role}")

        st.markdown("---")
        st.subheader("Navigation")
        
        # Logout Trigger
        if st.button("🚪 Logout", use_container_width=True):
            on_logout_callback()

        st.markdown("---")
        st.caption("RealtyCRM Enterprise v1.0")
        st.caption("Powered by FastAPI & AI Copilot")