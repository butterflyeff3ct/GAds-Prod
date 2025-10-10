# /app/navigation.py
import streamlit as st
from app.state import initialize_session_state
from app.dashboard_page import render_dashboard
from app.reports_page import render_reports
from app.attribution_page import render_attribution_analysis
from app.search_terms_page import render_search_terms_report
from app.planner_page import render_keyword_planner
from app.campaign_wizard import render_campaign_wizard
from app.data_inspector_page import render_data_inspector
from services.google_ads_client import GOOGLE_ADS_API_AVAILABLE
from app.auction_insights_page import render_auction_insights
from app.chatbot import render_dialogflow_chat

def render_sidebar():
    """Renders the main sidebar navigation and settings."""
    with st.sidebar:
        st.title("ADS SIMULATOR")
        
        if st.button("➕ Create New Campaign", type="primary", use_container_width=True):
            initialize_session_state() # Reset state for a new campaign
            st.session_state.campaign_step = 1
            st.rerun()

        st.markdown("---")
        
        # Use a key for the radio button to manage navigation state
        if 'page_selection' not in st.session_state:
            st.session_state.page_selection = "Dashboard"

        page = st.radio(
            "Navigation",
            ["Dashboard", "Reports", "Attribution", "Search Terms", "Auction Insights", "Planner"],
            key="page_selection"
        )
        
        st.markdown("---")
        st.subheader("⚙️ Settings")
        
        st.checkbox(
            "Use Google Ads API",
            value=st.session_state.get('use_api_data', GOOGLE_ADS_API_AVAILABLE),
            help="Use real data from Google Ads API if available.",
            key="use_api_data"
        )
        st.checkbox(
            "Use ML Bidding",
            value=st.session_state.get('use_ml_bidding', False),
            help="Enable machine learning for bid optimization.",
            key="use_ml_bidding"
        )
        
        st.markdown("---")
        
        # Cache Management
        st.subheader("🗑️ Cache Management")
        if st.button("Clear All Caches", use_container_width=True, help="Clear all cached data"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Caches cleared successfully")
            st.rerun()
        
        st.markdown("---")
        if st.secrets.get("dialogflow", {}).get("project_id"):
            st.subheader("💬 AI Assistant")
            st.info("Chat assistant is active in the bottom-right corner.")
            try:
                render_dialogflow_chat(
                    project_id=st.secrets.dialogflow.project_id,
                    agent_id=st.secrets.dialogflow.agent_id
                )
            except Exception as e:
                st.warning(f"Could not load chatbot: {e}")
                
    return page

def display_page(page: str):
    """Calls the appropriate render function based on page selection."""
    # Check for campaign launch flag and redirect to Dashboard
    if st.session_state.get('campaign_launched', False):
        st.session_state['campaign_launched'] = False
        # Force render Dashboard without modifying page_selection
        render_dashboard()
        return
    
    # If in the middle of campaign creation, always show the wizard
    if st.session_state.campaign_step > 0:
        render_campaign_wizard()
        return

    page_map = {
        "Dashboard": render_dashboard,
        "Reports": render_reports,
        "Attribution": render_attribution_analysis,
        "Search Terms": render_search_terms_report,
        "Auction Insights": render_auction_insights,
        "Planner": render_keyword_planner,
    }
    # Get the function from the map and call it
    render_func = page_map.get(page)
    if render_func:
        render_func()
    else:
        st.error("Page not found.")
