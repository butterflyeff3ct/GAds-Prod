# /app/navigation.py
import streamlit as st

# Safe imports with fallbacks
try:
    from app.state import initialize_session_state
except ImportError:
    def initialize_session_state():
        """Fallback initialization if state module fails"""
        pass

try:
    from app.dashboard_page import render_dashboard
    from app.reports_page import render_reports
    from app.attribution_page import render_attribution_analysis
    from app.search_terms_page import render_search_terms_report
    from app.planner_page import render_keyword_planner
    from app.campaign_wizard import render_campaign_wizard
    from app.auction_insights_page import render_auction_insights
    from app.chatbot import render_dialogflow_chat
    from auth.user_dashboard import render_user_dashboard
    
except ImportError as e:
    st.error(f"Error importing page modules: {e}")
    # Fallback functions
    def render_dashboard():
        st.error("Dashboard not available")
    def render_reports():
        st.error("Reports not available")
    def render_attribution_analysis():
        st.error("Attribution analysis not available")
    def render_search_terms_report():
        st.error("Search terms report not available")
    def render_keyword_planner():
        st.error("Keyword planner not available")
    def render_campaign_wizard():
        st.error("Campaign wizard not available")
    def render_auction_insights():
        st.error("Auction insights not available")
    def render_dialogflow_chat():
        st.error("Chatbot not available")
    def render_user_dashboard():
        st.error("User dashboard not available")

# API Test page removed from navigation

try:
    from services.google_ads_client import GOOGLE_ADS_API_AVAILABLE
except ImportError:
    GOOGLE_ADS_API_AVAILABLE = False

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
            ["Dashboard", "Reports", "Attribution", "Search Terms", "Auction Insights", "Planner", "User Dashboard"],
            key="page_selection"
        )
        
        # User Authentication & Info
        try:
            from auth.user_dashboard import render_compact_user_info
            render_compact_user_info()
        except ImportError:
            st.warning("⚠️ Authentication system not available")
        
        # Real-Time API Usage Dashboard
        try:
            from monitor.api_usage_dashboard import render_compact_usage
            render_compact_usage()
        except ImportError:
            # Fallback to old usage stats
            try:
                from app.sidebar_stats import render_compact_usage
                render_compact_usage()
            except ImportError:
                st.warning("⚠️ API monitoring not available")
        
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
        if st.button("Clear All Caches", use_container_width=True, help="Clear all cached data from @st.cache_data and @st.cache_resource functions"):
            # Clear all caches using the disabled functions (they do nothing but show success)
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache clearing is disabled to prevent popups. Use the sidebar button for manual cache management.")
            st.rerun()
        
        st.markdown("---")
        st.subheader("💬 AI Assistant")
        if st.secrets.get("dialogflow", {}).get("project_id"):
            st.info("Chat assistant is active in the bottom-right corner.")
            try:
                render_dialogflow_chat(
                    project_id=st.secrets.dialogflow.project_id,
                    agent_id=st.secrets.dialogflow.agent_id
                )
            except Exception as e:
                st.warning(f"Could not load Dialogflow chatbot: {e}")
                st.info("🤖 Using built-in assistant.")
        else:
            st.info("🤖 Built-in AI assistant is ready to help!")
                
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
        "User Dashboard": render_user_dashboard,
    }
    # Get the function from the map and call it
    render_func = page_map.get(page)
    if render_func:
        render_func()
    else:
        st.error("Page not found.")