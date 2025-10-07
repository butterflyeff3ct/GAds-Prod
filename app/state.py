# /app/state.py
import streamlit as st
from datetime import date
from data_models.schemas import BiddingStrategy
from app.state_manager import StateManager

# Static data for campaign creation
OBJECTIVES_ENHANCED = {
    "Sales": {
        "icon": "💰", "desc": "Drive sales online, in app, by phone, or in store",
        "conversion_types": ["purchase", "add_to_cart"],
        "bidding_strategies": ["target_roas", "maximize_conversion_value"]
    },
    "Leads": {
        "icon": "👥", "desc": "Get leads and other conversions by encouraging customers to take action",
        "conversion_types": ["lead", "signup"],
        "bidding_strategies": ["target_cpa", "maximize_conversions"]
    },
    "Website traffic": {
        "icon": "🌐", "desc": "Get the right people to visit your website.",
        "conversion_types": ["view_content"],
        "bidding_strategies": ["maximize_clicks", "manual_cpc"]
    },
    # Add other objectives from the screenshot for visual completeness
    "App promotion": {"icon": "📱", "desc": "Get more installs, engagement, and pre-registration for your app", "conversion_types": [], "bidding_strategies": []},
    "Awareness and consideration": {"icon": "📢", "desc": "Reach a broad audience and build interest", "conversion_types": [], "bidding_strategies": []},
    "Local store visits and promotions": {"icon": "🏪", "desc": "Drive visits to local stores", "conversion_types": [], "bidding_strategies": []},
}

GEO_LOCATIONS = {
    "United States": {"geo_id": "2840"}, "California": {"geo_id": "21137"},
    "New York": {"geo_id": "21167"}, "Texas": {"geo_id": "21175"},
    "Canada": {"geo_id": "2124"}, "United Kingdom": {"geo_id": "2826"},
    "Germany": {"geo_id": "2276"}, "Australia": {"geo_id": "2036"},
}

AUDIENCE_SEGMENTS = {
    "Remarketing": ["All Visitors", "Cart Abandoners", "Past Purchasers"],
    "In-Market": ["Auto Buyers", "Travel", "Technology"],
    "Affinity": ["Sports Fans", "Luxury Shoppers"]
}

def initialize_session_state():
    """Initializes all required session state variables for the app using StateManager."""
    # Use centralized state manager
    StateManager.initialize()
    
    # Legacy initialization for backward compatibility
    if 'new_campaign_config' not in st.session_state:
        st.session_state.new_campaign_config = {
            # Basic Settings
            "objective": None,
            "campaign_type": "Search",
            "reach_methods": ["Website visits"],
            "campaign_name": "", 
            "daily_budget": 100.0, 
            "monthly_budget_cap": None,
            "delivery_method": "standard",
            # Scheduling
            "start_date": date.today(), 
            "end_date": None,
            "ad_schedule": {"enabled": False, "hours": {}},
            # Bidding
            "bidding_strategy": BiddingStrategy.MAXIMIZE_CLICKS.value,
            "target_cpa": 20.0, 
            "target_roas": 4.0, 
            "max_cpc_limit": 2.00,
            # Networks
            "networks": ["google_search"],
            # Targeting
            "locations": ["United States"], 
            "audiences": [],
            "device_bid_adjustments": {"mobile": 1.0, "desktop": 1.0, "tablet": 0.95},
            # Conversion Tracking
            "conversion_tracking": {"attribution_model": "last_click", "conversion_types": []},
            # Ad Groups
            "ad_groups": [{"name": "Ad Group 1", "keywords": "", "headlines": [], "descriptions": [], "extensions": {}}],
            "negative_keywords": []
        }