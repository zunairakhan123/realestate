# import streamlit as st
# from api_client import APIClient
# from components.copilot_ui import render_copilot


# def render_admin_dashboard():
#     st.title("Admin Control Center")
    
#     tab1, tab2, tab3 = st.tabs(["📊 Analytics & Leads", "👥 Agent Management", "🤖 AI Copilot"])

#     with tab1:
#         st.header("System Lead Overview")
        
#         response = APIClient.get("/leads/")
#         leads = response.get("items", []) if isinstance(response, dict) else response

#         if isinstance(leads, list):
#             st.metric("Total System Leads", len(leads))
#             if leads:
#                 for lead in leads:
#                     st.write(f"**ID:** {lead.get('id')} | **Status:** {lead.get('status')} | **Agent:** {lead.get('agent_id')} | **Customer:** {lead.get('customer_id')}")
#             else:
#                 st.info("No leads currently in the system.")
#         else:
#             st.error("Could not fetch system leads.")

#     with tab2:
#         st.header("Agent Accounts Management")
#         st.write("Provision new real estate agent credentials securely.")

#         with st.form("create_agent_form"):
#             agent_name = st.text_input("Agent Name") # <-- Added name input
#             agent_email = st.text_input("Agent Email")
#             agent_password = st.text_input("Temporary Password", type="password")
#             submit_agent = st.form_submit_button("Create Agent Account")

#             if submit_agent:
#                 if not agent_name or not agent_email or not agent_password:
#                     st.error("Please fill in all fields (Name, Email, and Password).")
#                 else:
#                     payload = {
#                         "name": agent_name, # <-- Included name in payload
#                         "email": agent_email,
#                         "password": agent_password
#                     }
#                     res = APIClient.post("/auth/admin/agents", data=payload)
                    
#                     if isinstance(res, dict) and "email" in res:
#                         st.success(f"Successfully created agent account for: {res.get('email')}")
#                     else:
#                         error_msg = res.get("error") or res.get("detail", "Failed to create agent.")
#                         st.error(error_msg)

#     with tab3:
#         st.markdown("### Admin AI Copilot Assistant")
#         st.info("As an Admin, your Copilot has full visibility across all system leads, properties, and customer records.")
#         render_copilot()

import streamlit as st
from api_client import APIClient
from components.copilot_ui import render_copilot


def render_admin_dashboard():
    st.title("Admin Control Center")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics & Leads", "🏠 Properties", "👥 Agent Management", "🤖 AI Copilot"])

    with tab1:
        st.header("System Lead Overview")
        
        response = APIClient.get("/leads/")
        leads = response.get("items", []) if isinstance(response, dict) else response

        if isinstance(leads, list):
            st.metric("Total System Leads", len(leads))
            st.divider()
            
            if leads:
                # Render system leads in a clean 2-column card grid
                cols = st.columns(2)
                for idx, lead in enumerate(leads):
                    col = cols[idx % 2]
                    with col:
                        with st.container(border=True):
                            st.subheader(f"Lead #{str(lead.get('id'))[:8]}...")
                            
                            # Status badge coloring logic
                            status = str(lead.get('status', 'NEW')).upper()
                            if status in ['NEW', 'PENDING']:
                                st.markdown(f"**Status:** `🔵 {status}`")
                            else:
                                st.markdown(f"**Status:** `🟢 {status}`")
                                
                            st.text(f"Customer ID: {lead.get('customer_id')}")
                            st.text(f"Property ID: {lead.get('property_id')}")
                            st.text(f"Assigned Agent: {lead.get('agent_id') or 'Unassigned'}")
                            
                            if lead.get('notes'):
                                st.caption(f"Notes: {lead.get('notes')}")
            else:
                st.info("No leads currently in the system.")
        else:
            st.error("Could not fetch system leads.")

    with tab2:
        st.header("Real Estate Portfolio")
        
        prop_response = APIClient.get("/properties/")
        properties = prop_response.get("items", []) if isinstance(prop_response, dict) else (prop_response if isinstance(prop_response, list) else [])

        if properties:
            cols = st.columns(3)
            for idx, prop in enumerate(properties):
                col = cols[idx % 3]
                with col:
                    with st.container(border=True):
                        img_url = prop.get('image_url')
                        if img_url and isinstance(img_url, str) and img_url.lower() != "string" and img_url.startswith("http"):
                            st.image(img_url, use_column_width=True) # <-- Fixed to use_column_width
                        else:
                            st.info("🏠 [No Image Available]")
                            
                        st.subheader(prop.get('address', 'Property'))
                        st.markdown(f"**City:** {prop.get('city')}")
                        st.markdown(f"**Price:** ${prop.get('price', 0):,.2f}")
                        st.text(f"Type: {prop.get('property_type')} | Beds: {prop.get('bedrooms')}")
        else:
            st.info("No properties found or endpoint not indexed yet.")

    with tab3:
        st.header("Agent Accounts Management")
        st.write("Provision new real estate agent credentials securely.")

        with st.form("create_agent_form"):
            agent_name = st.text_input("Agent Name")
            agent_email = st.text_input("Agent Email")
            agent_password = st.text_input("Temporary Password", type="password")
            submit_agent = st.form_submit_button("Create Agent Account")

            if submit_agent:
                if not agent_name or not agent_email or not agent_password:
                    st.error("Please fill in all fields (Name, Email, and Password).")
                else:
                    payload = {
                        "name": agent_name,
                        "email": agent_email,
                        "password": agent_password
                    }
                    res = APIClient.post("/auth/admin/agents", data=payload)
                    
                    if isinstance(res, dict) and "email" in res:
                        st.success(f"Successfully created agent account for: {res.get('email')}")
                    else:
                        error_msg = res.get("error") or res.get("detail", "Failed to create agent.")
                        st.error(error_msg)

    with tab4:
        st.markdown("### Admin AI Copilot Assistant")
        st.info("As an Admin, your Copilot has full visibility across all system leads, properties, and customer records.")
        render_copilot()