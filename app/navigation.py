# /app/navigation.py
# OPTIMIZED VERSION - Lazy loading for all pages to reduce startup time

import streamlit as st

# ========================================
# LAZY PAGE IMPORTS - Load only when needed
# ========================================

def lazy_import_dashboard():
    """Lazy import dashboard page"""
    from app.dashboard_page import render_dashboard
    return render_dashboard

def lazy_import_reports():
    """Lazy import reports page"""
    from app.reports_page import render_reports
    return render_reports

def lazy_import_attribution():
    """Lazy import attribution page"""
    from app.attribution_page import render_attribution_analysis
    return render_attribution_analysis

def lazy_import_search_terms():
    """Lazy import search terms page"""
    from app.search_terms_page import render_search_terms_report
    return render_search_terms_report

def lazy_import_planner():
    """Lazy import planner page"""
    from app.planner_page import render_keyword_planner
    return render_keyword_planner

def lazy_import_campaign_wizard():
    """Lazy import campaign wizard"""
    from app.campaign_wizard import render_campaign_wizard
    return render_campaign_wizard

def lazy_import_auction_insights():
    """Lazy import auction insights"""
    from app.auction_insights_page import render_auction_insights
    return render_auction_insights

def lazy_import_admin():
    """Lazy import admin components"""
    from app.admin.admin_controller import is_admin_user, initialize_admin_state
    from app.admin.admin_dashboard_secure import render_admin_dashboard
    return is_admin_user, initialize_admin_state, render_admin_dashboard

def lazy_import_wizard_utils():
    """Lazy import wizard utilities"""
    from app.wizard_components.wizard_navigation import reset_wizard_navigation
    return reset_wizard_navigation

def lazy_import_quota_system():
    """Lazy import quota system"""
    from app.quota_system import render_quota_metrics
    return render_quota_metrics

def lazy_import_state():
    """Lazy import state initialization"""
    from app.state import initialize_session_state
    return initialize_session_state

def lazy_import_google_ads_check():
    """Lazy import Google Ads API availability check"""
    from services.google_ads_client import GOOGLE_ADS_API_AVAILABLE
    return GOOGLE_ADS_API_AVAILABLE

# ========================================
# SIDEBAR RENDERING
# ========================================

def render_sidebar():
    """Renders the main sidebar navigation and settings."""
    
    # CHECK IF IN WIZARD MODE
    in_wizard_mode = st.session_state.get('campaign_step', 0) > 0
    
    with st.sidebar:
        st.title("ADS SIMULATOR")
        
        # Only show Create Campaign button if NOT in wizard mode
        if not in_wizard_mode:
            if st.button("➕ Create New Campaign", type="primary", use_container_width=True):
                # Lazy load initialization functions
                initialize_session_state = lazy_import_state()
                reset_wizard_navigation = lazy_import_wizard_utils()
                
                initialize_session_state()  # Reset state for a new campaign
                reset_wizard_navigation()  # Reset wizard tracking
                st.session_state.campaign_step = 1
                st.rerun()

            st.markdown("---")
            
            # Main navigation - HIDE in wizard mode
            if 'page_selection' not in st.session_state:
                st.session_state.page_selection = "Dashboard"

            page = st.radio(
                "Navigation",
                ["Dashboard", "Reports", "Attribution", "Search Terms", "Auction Insights", "Planner"],
                key="page_selection"
            )
            
            st.markdown("---")
            
            # Admin Access (ONLY for admins) - HIDE in wizard mode
            # Lazy load admin check
            is_admin_user, initialize_admin_state, _ = lazy_import_admin()
            initialize_admin_state()
            
            if is_admin_user():
                st.subheader("👨‍💼 Admin Tools")
                if st.button(
                    "📊 Admin Dashboard",
                    use_container_width=True,
                    type="secondary",
                    help="Access administrative features"
                ):
                    st.session_state.show_admin_dashboard = True
                    st.rerun()
            
            st.markdown("---")
            st.subheader("⚙️ Settings")
            
            # Lazy check for Google Ads API
            GOOGLE_ADS_API_AVAILABLE = lazy_import_google_ads_check()
            
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
            
            # Cache Management - HIDE in wizard mode
            st.subheader("🗑️ Cache Management")
            if st.button("Clear All Caches", use_container_width=True, help="Clear all cached data"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Caches cleared successfully")
                st.rerun()
            
            # Lazy load quota display
            render_quota_metrics = lazy_import_quota_system()
            render_quota_metrics(location="sidebar")
            
        else:
            # IN WIZARD MODE - Show minimal info
            st.caption("Creating new campaign...")
            st.caption("Use the step navigation below to move through the wizard")
        
        # NOTE: Wizard step navigation is rendered by the wizard itself
        # via render_wizard_step_sidebar() in campaign_wizard.py
                
    return st.session_state.get('page_selection', "Dashboard") if not in_wizard_mode else None


# ========================================
# PAGE DISPLAY - Lazy loading
# ========================================

def display_page(page: str):
    """Calls the appropriate render function based on page selection using lazy loading."""
    
    # Lazy load admin functions
    is_admin_user, initialize_admin_state, render_admin_dashboard = lazy_import_admin()
    
    # Initialize admin state
    initialize_admin_state()
    
    # NEW - Check if admin dashboard should be shown (FIRST PRIORITY)
    if st.session_state.get('show_admin_dashboard', False) and is_admin_user():
        render_admin_dashboard()
        return
    
    # Check for campaign launch flag and redirect to Dashboard
    if st.session_state.get('campaign_launched', False):
        st.session_state['campaign_launched'] = False
        # Lazy load and force render Dashboard
        render_dashboard = lazy_import_dashboard()
        render_dashboard()
        return
    
    # If in the middle of campaign creation, always show the wizard
    if st.session_state.get('campaign_step', 0) > 0:
        render_campaign_wizard = lazy_import_campaign_wizard()
        render_campaign_wizard()
        return

    # LAZY LOAD PAGE MAP - Only import the page that's needed
    page_loaders = {
        "Dashboard": lazy_import_dashboard,
        "Reports": lazy_import_reports,
        "Attribution": lazy_import_attribution,
        "Search Terms": lazy_import_search_terms,
        "Auction Insights": lazy_import_auction_insights,
        "Planner": lazy_import_planner,
    }
    
    # Get the lazy loader for the requested page
    page_loader = page_loaders.get(page)
    
    if page_loader:
        # Load the page function only when needed
        render_func = page_loader()
        render_func()
    else:
        st.error("Page not found.")
