# import streamlit as st
# from api_client import APIClient
# from components.copilot_ui import render_copilot


# def render_customer_dashboard():
#     st.title(f"Welcome, {st.session_state.get('user_email', 'Customer')}!")
    
#     tab1, tab2 = st.tabs(["🏠 Browse Properties", "📋 My Leads"])

#     with tab1:
#         st.header("Available Properties")
#         city_filter = st.text_input("Filter by City")
        
#         response = APIClient.get("/properties/", params={"city": city_filter} if city_filter else {})
        
#         # Extract the list of properties from the 'items' key of the paginated dictionary response
#         properties = response.get("items", []) if isinstance(response, dict) else response

#         if isinstance(properties, list) and properties:
#             for prop in properties:
#                 with st.container():
#                     st.markdown(f"### {prop.get('address')} ({prop.get('city')})")
#                     st.write(f"**Price:** ${prop.get('price'):,.2f} | **Bedrooms:** {prop.get('bedrooms')} | **Type:** {prop.get('property_type')}")
                    
#                     if st.button("Mark as Interested", key=f"prop_{prop.get('id')}"):
#                         lead_payload = {"property_id": prop.get('id')}
#                         res = APIClient.post("/leads/", data=lead_payload)
#                         if "error" in res:
#                             st.error(res["error"])
#                         else:
#                             st.success("Successfully expressed interest! Lead created.")
#                     st.divider()
#         else:
#             st.info("No properties found.")

#     with tab2:
#         st.header("My Leads")
#         response = APIClient.get("/leads/")
        
#         # Extract items if the backend returns a paginated dictionary structure {"total": X, "items": [...]}
#         leads = response.get("items", []) if isinstance(response, dict) else response

#         if isinstance(leads, list) and leads:
#             for lead in leads:
#                 st.write(f"**Lead ID:** {lead.get('id')} | **Status:** {lead.get('status')} | **Property ID:** {lead.get('property_id')}")
#         else:
#             st.info("No active leads found.")

#     # with tab3:
#     #     render_copilot()

import streamlit as st
from api_client import APIClient
from components.copilot_ui import render_copilot


def render_customer_dashboard():
    st.title(f"Welcome, {st.session_state.get('user_email', 'Customer')}!")
    
    tab1, tab2, tab3 = st.tabs(["🏠 Browse Properties", "📋 My Leads", "🤖 AI Copilot"])

    with tab1:
        st.header("Available Real Estate Portfolio")
        city_filter = st.text_input("Filter by City", placeholder="e.g. Lahore")
        
        response = APIClient.get("/properties/", params={"city": city_filter} if city_filter else {})
        properties = response.get("items", []) if isinstance(response, dict) else response

        if isinstance(properties, list) and properties:
            st.divider()
            # Arrange property cards in a 3-column responsive grid
            cols = st.columns(3)
            for idx, prop in enumerate(properties):
                col = cols[idx % 3]
                with col:
                    with st.container(border=True):
                        # Check if image_url exists, is a valid string, and isn't just a dummy placeholder like "string"
                        img_url = prop.get('image_url')
                        if img_url and isinstance(img_url, str) and img_url.lower() != "string" and img_url.startswith("http"):
                            st.image(img_url, use_column_width=True)
                        else:
                            # Optional: display a clean placeholder or skip image rendering
                            st.info("🏠 [No Image Available]")
                        
                        st.subheader(prop.get('address', 'Property'))
                        st.markdown(f"**City:** {prop.get('city')}")
                        st.markdown(f"**Price:** ${prop.get('price', 0):,.2f}")
                        st.text(f"Type: {prop.get('property_type')} | Beds: {prop.get('bedrooms')}")
                        
                        st.divider()
                        
                        if st.button("Mark as Interested", key=f"prop_btn_{prop.get('id')}", use_container_width=True):
                            lead_payload = {"property_id": prop.get('id')}
                            res = APIClient.post("/leads/", data=lead_payload)
                            if isinstance(res, dict) and "error" in res:
                                st.error(res["error"])
                            else:
                                st.success("Interest registered! Lead created.")
        else:
            st.info("No properties found matching your criteria.")

    with tab2:
        st.header("My Expressed Interest Leads")
        response = APIClient.get("/leads/")
        leads = response.get("items", []) if isinstance(response, dict) else response

        if isinstance(leads, list) and leads:
            st.metric("Total Active Leads", len(leads))
            st.divider()
            
            # Render leads in a neat 2-column card view
            cols = st.columns(2)
            for idx, lead in enumerate(leads):
                col = cols[idx % 2]
                with col:
                    with st.container(border=True):
                        st.subheader(f"Lead #{str(lead.get('id'))[:8]}...")
                        
                        status = str(lead.get('status', 'NEW')).upper()
                        if status in ['NEW', 'PENDING']:
                            st.markdown(f"**Status:** `🔵 {status}`")
                        else:
                            st.markdown(f"**Status:** `🟢 {status}`")
                            
                        st.text(f"Property ID: {lead.get('property_id')}")
                        if lead.get('notes'):
                            st.caption(f"Notes: {lead.get('notes')}")
        else:
            st.info("You haven't expressed interest in any properties yet. Browse tab 1 to get started!")

    with tab3:
        st.markdown("### Customer Assistant")
        st.info("Ask questions about properties or check your lead statuses using the AI Copilot.")
        render_copilot()