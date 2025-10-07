# /app/state_manager.py
"""
Centralized State Management
Cleaner, type-safe state management for the entire application.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
from datetime import date
from data_models.schemas import BiddingStrategy
from dataclasses import dataclass, asdict
import json

@dataclass
class CampaignConfig:
    """Type-safe campaign configuration."""
    # Basic Settings
    objective: Optional[str] = None
    campaign_type: str = "Search"
    campaign_name: str = ""
    
    # Budget
    daily_budget: float = 100.0
    budget_type: str = "daily"
    total_budget: float = 3000.0
    monthly_budget_cap: Optional[float] = None
    delivery_method: str = "standard"
    
    # Bidding
    bidding_strategy: str = "maximize_clicks"
    bidding_focus: str = "conversions"
    target_cpa: float = 50.0
    target_roas: float = 4.0
    set_target_cpa: bool = False
    
    # Targeting
    locations: List[str] = None
    languages: List[str] = None
    audiences: List[str] = None
    device_bid_adjustments: Dict[str, float] = None
    
    # Networks
    networks: List[str] = None
    include_search_partners: bool = True
    include_display: bool = False
    
    # Scheduling
    start_date: str = None
    end_date: Optional[str] = None
    has_end_date: bool = False
    use_ad_schedule: bool = False
    
    # Ad Groups
    ad_groups: List[Dict] = None
    
    def __post_init__(self):
        """Set defaults for mutable types."""
        if self.locations is None:
            self.locations = ["United States"]
        if self.languages is None:
            self.languages = ["English"]
        if self.audiences is None:
            self.audiences = []
        if self.device_bid_adjustments is None:
            self.device_bid_adjustments = {"mobile": 1.0, "desktop": 1.0, "tablet": 0.95}
        if self.networks is None:
            self.networks = ["google_search"]
        if self.ad_groups is None:
            self.ad_groups = []
        if self.start_date is None:
            self.start_date = date.today().isoformat()

class StateManager:
    """
    Centralized state management for the application.
    Provides type-safe access to session state.
    """
    
    # State keys
    CAMPAIGN_STEP = 'campaign_step'
    CAMPAIGN_CONFIG = 'new_campaign_config'
    SIMULATION_RESULTS = 'simulation_results'
    PACING_HISTORY = 'pacing_history'
    USE_API_DATA = 'use_api_data'
    USE_ML_BIDDING = 'use_ml_bidding'
    SELECTED_KEYWORDS = 'selected_keywords_for_campaign'
    DASHBOARD_METRICS = 'dashboard_metrics'
    PAGE_SELECTION = 'page_selection'
    
    @staticmethod
    def initialize():
        """Initialize all required session state variables."""
        defaults = {
            StateManager.CAMPAIGN_STEP: 0,
            StateManager.SIMULATION_RESULTS: None,
            StateManager.PACING_HISTORY: [],
            StateManager.USE_API_DATA: True,
            StateManager.USE_ML_BIDDING: False,
            StateManager.SELECTED_KEYWORDS: [],
            StateManager.DASHBOARD_METRICS: ['Clicks', 'Impressions', 'Avg. CPC', 'Cost'],
            StateManager.PAGE_SELECTION: 'Dashboard'
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Initialize campaign config separately (complex object)
        if StateManager.CAMPAIGN_CONFIG not in st.session_state:
            st.session_state[StateManager.CAMPAIGN_CONFIG] = asdict(CampaignConfig())
    
    @staticmethod
    def get_campaign_config() -> Dict:
        """Get campaign configuration."""
        return st.session_state.get(StateManager.CAMPAIGN_CONFIG, asdict(CampaignConfig()))
    
    @staticmethod
    def update_campaign_config(updates: Dict):
        """Update campaign configuration with new values."""
        config = StateManager.get_campaign_config()
        config.update(updates)
        st.session_state[StateManager.CAMPAIGN_CONFIG] = config
    
    @staticmethod
    def reset_campaign_config():
        """Reset campaign configuration to defaults."""
        st.session_state[StateManager.CAMPAIGN_CONFIG] = asdict(CampaignConfig())
        st.session_state[StateManager.CAMPAIGN_STEP] = 0
    
    @staticmethod
    def get_simulation_results() -> Optional[Any]:
        """Get simulation results dataframe."""
        return st.session_state.get(StateManager.SIMULATION_RESULTS)
    
    @staticmethod
    def set_simulation_results(results):
        """Set simulation results."""
        st.session_state[StateManager.SIMULATION_RESULTS] = results
    
    @staticmethod
    def get_campaign_step() -> int:
        """Get current campaign wizard step."""
        return st.session_state.get(StateManager.CAMPAIGN_STEP, 0)
    
    @staticmethod
    def set_campaign_step(step: int):
        """Set campaign wizard step."""
        st.session_state[StateManager.CAMPAIGN_STEP] = step
    
    @staticmethod
    def next_step():
        """Move to next wizard step."""
        current = StateManager.get_campaign_step()
        StateManager.set_campaign_step(current + 1)
    
    @staticmethod
    def previous_step():
        """Move to previous wizard step."""
        current = StateManager.get_campaign_step()
        StateManager.set_campaign_step(max(0, current - 1))
    
    @staticmethod
    def is_using_api_data() -> bool:
        """Check if using Google Ads API data."""
        return st.session_state.get(StateManager.USE_API_DATA, True)
    
    @staticmethod
    def is_using_ml_bidding() -> bool:
        """Check if ML bidding is enabled."""
        return st.session_state.get(StateManager.USE_ML_BIDDING, False)
    
    @staticmethod
    def get_selected_keywords() -> List[str]:
        """Get keywords selected from planner."""
        return st.session_state.get(StateManager.SELECTED_KEYWORDS, [])
    
    @staticmethod
    def add_selected_keywords(keywords: List[str]):
        """Add keywords to selection."""
        current = StateManager.get_selected_keywords()
        current.extend(keywords)
        st.session_state[StateManager.SELECTED_KEYWORDS] = list(set(current))  # Remove duplicates
    
    @staticmethod
    def clear_selected_keywords():
        """Clear selected keywords."""
        st.session_state[StateManager.SELECTED_KEYWORDS] = []
    
    @staticmethod
    def export_state() -> str:
        """Export current state as JSON (for save/load)."""
        exportable_state = {
            'campaign_config': StateManager.get_campaign_config(),
            'campaign_step': StateManager.get_campaign_step(),
            'use_api_data': StateManager.is_using_api_data(),
            'use_ml_bidding': StateManager.is_using_ml_bidding()
        }
        return json.dumps(exportable_state, indent=2, default=str)
    
    @staticmethod
    def import_state(json_str: str):
        """Import state from JSON."""
        try:
            state_dict = json.loads(json_str)
            
            if 'campaign_config' in state_dict:
                st.session_state[StateManager.CAMPAIGN_CONFIG] = state_dict['campaign_config']
            
            if 'campaign_step' in state_dict:
                st.session_state[StateManager.CAMPAIGN_STEP] = state_dict['campaign_step']
            
            if 'use_api_data' in state_dict:
                st.session_state[StateManager.USE_API_DATA] = state_dict['use_api_data']
            
            if 'use_ml_bidding' in state_dict:
                st.session_state[StateManager.USE_ML_BIDDING] = state_dict['use_ml_bidding']
            
            return True
        except Exception as e:
            st.error(f"Failed to import state: {e}")
            return False
    
    @staticmethod
    def get_dashboard_metrics() -> List[str]:
        """Get selected dashboard metrics."""
        return st.session_state.get(StateManager.DASHBOARD_METRICS, 
                                    ['Clicks', 'Impressions', 'Avg. CPC', 'Cost'])
    
    @staticmethod
    def update_dashboard_metric(index: int, metric: str):
        """Update a specific dashboard metric."""
        metrics = StateManager.get_dashboard_metrics()
        if 0 <= index < len(metrics):
            metrics[index] = metric
            st.session_state[StateManager.DASHBOARD_METRICS] = metrics
