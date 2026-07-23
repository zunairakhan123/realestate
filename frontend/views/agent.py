# import streamlit as st
# from api_client import APIClient
# from components.copilot_ui import render_copilot

# def render_agent_dashboard():
#     st.title("Agent Dashboard")
    
#     tab1, tab2 = st.tabs(["📋 Assigned Leads", "🤖 AI Copilot"])

#     with tab1:
#         st.header("Leads Assigned to You")
        
#         response = APIClient.get("/leads/") 
        
#         leads = response.get("items", []) if isinstance(response, dict) else response

#         if isinstance(leads, list) and leads:
#             for lead in leads:
#                 st.write(f"**Lead ID:** {lead.get('id')} | **Status:** {lead.get('status')} | **Customer ID:** {lead.get('customer_id')}")
#         else:
#             st.info("No leads assigned currently.")

#     with tab2:
#         render_copilot()

import streamlit as st
from api_client import APIClient
from components.copilot_ui import render_copilot


def render_agent_dashboard():
    st.title("Agent Dashboard")
    
    tab1, tab2 = st.tabs(["📋 Assigned Leads", "🤖 AI Copilot"])

    with tab1:
        st.header("Leads Assigned to You")
        
        response = APIClient.get("/leads/") 
        leads = response.get("items", []) if isinstance(response, dict) else response

        if isinstance(leads, list) and leads:
            st.metric("Total Assigned Leads", len(leads))
            st.divider()
            
            # Display leads in a grid/card layout (2 columns)
            cols = st.columns(2)
            for idx, lead in enumerate(leads):
                col = cols[idx % 2]
                with col:
                    with st.container(border=True):
                        st.subheader(f"Lead #{str(lead.get('id'))[:8]}...")
                        
                        # Status badge coloring logic
                        status = lead.get('status', 'NEW')
                        if status.lower() in ['new', 'pending']:
                            st.markdown(f"**Status:** `🔵 {status.upper()}`")
                        elif status.lower() in ['qualified', 'accepted', 'closed']:
                            st.markdown(f"**Status:** `🟢 {status.upper()}`")
                        else:
                            st.markdown(f"**Status:** `🟠 {status.upper()}`")

                        st.text(f"Customer ID: {lead.get('customer_id')}")
                        st.text(f"Property ID: {lead.get('property_id')}")
                        
                        if lead.get('notes'):
                            st.caption(f"Notes: {lead.get('notes')}")
        else:
            st.info("No leads assigned currently.")

    with tab2:
        render_copilot()