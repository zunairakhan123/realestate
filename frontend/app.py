"""
Main Streamlit Application Entry Point

Manages authentication state, token storage, and role-based view dispatching.
"""
import sys
import os

# Add the frontend directory to Python's module search path
frontend_dir = os.path.dirname(os.path.abspath(__file__))
if frontend_dir not in sys.path:
    sys.path.append(frontend_dir)

import streamlit as st
from api_client import APIClient
from components.sidebar import render_sidebar
from views.customer import render_customer_dashboard
from views.agent import render_agent_dashboard
from views.admin import render_admin_dashboard
from config import BACKEND_API_URL


st.set_page_config(page_title="RealtyCRM Portal", page_icon="🏢", layout="wide")

# Load Custom CSS Asset
import os
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Initialize session state variables
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None


def logout():
    st.session_state.access_token = None
    st.session_state.user_role = None
    st.session_state.user_email = None
    st.rerun()


def render_auth_portal():
    st.title("🏢 RealtyCRM Portal")
    auth_tab_login, auth_tab_register = st.tabs(["Login", "Customer Register"])

    with auth_tab_login:
        st.subheader("Sign In")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            # FastAPI OAuth2PasswordRequestForm expects form-data with username & password
            try:
                import httpx
                response = httpx.post(
                    f"{BACKEND_API_URL}/auth/login",
                    data={"username": email, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.access_token = data.get("access_token")
                    
                    # Fetch user profile to determine role
                    user_res = APIClient.get("/auth/me")
                    if isinstance(user_res, dict) and "role" in user_res:
                        st.session_state.user_role = user_res.get("role").lower()
                        st.session_state.user_email = user_res.get("email")
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Failed to retrieve user profile metadata.")
                else:
                    st.error("Invalid credentials.")
            except Exception as e:
                st.error(f"Connection error: {e}")

    with auth_tab_register:
        st.subheader("New Customer Signup")
        reg_name = st.text_input("Full Name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_phone = st.text_input("Phone")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        
        # Changed to a dropdown matching backend expected enum values ('Cash' or 'Cheque')
        reg_payment = st.selectbox("Payment Method", options=["Cash", "Cheque"], key="reg_payment")

        if st.button("Register Account"):
            payload = {
                "name": reg_name,
                "email": reg_email,
                "phone": reg_phone,
                "password": reg_password,
                "payment": reg_payment
            }
            res = APIClient.post("/customers/", data=payload)
            if "error" in res:
                st.error(res["error"])
            else:
                st.success("Registration successful! You can now log in.")

def main():
    if not st.session_state.access_token:
        render_auth_portal()
    else:
        # Render modular sidebar component
        render_sidebar(logout)

        # Render role-specific dashboard based solely on backend-issued role
        role = st.session_state.user_role
        if role == "customer":
            render_customer_dashboard()
        elif role == "agent":
            render_agent_dashboard()
        elif role == "admin":
            render_admin_dashboard()
        else:
            st.error(f"Unknown user role assigned: {role}")


if __name__ == "__main__":
    main()