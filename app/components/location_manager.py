# /core/impression_share_bidding.py
"""
Target Impression Share Bidding Strategy
Automatically adjusts bids to achieve a target impression share.
"""

from typing import Dict, Optional
from dataclasses import dataclass
import streamlit as st

@dataclass
class ImpressionShareTarget:
    """Target impression share configuration."""
    target_percentage: float  # e.g., 65.0 for 65%
    location: str  # "anywhere", "top_of_page", "absolute_top"
    max_cpc_bid_limit: Optional[float] = None  # Cap on bids

class TargetImpressionShareBidding:
    """
    Bidding strategy that optimizes for impression share.
    
    How it works:
    1. Monitor actual impression share
    2. If below target → increase bids
    3. If above target → decrease bids (save money)
    4. Respect max CPC limit
    """
    
    def __init__(self, target: ImpressionShareTarget):
        self.target = target
        self.current_is = 0.0
        self.bid_multiplier = 1.0
        self.learning_rate = 0.15
        
    def update_impression_share(self, actual_is: float):
        """Update with current impression share data."""
        self.current_is = actual_is
        
    def calculate_bid(self, base_bid: float, current_position: float,
                     current_is: float, competitor_density: float) -> float:
        """
        Calculate bid to achieve target impression share.
        
        Args:
            base_bid: Starting bid
            current_position: Current average position
            current_is: Current impression share (0-100)
            competitor_density: How competitive the auction is
        
        Returns:
            Adjusted bid to reach target IS
        """
        
        # Calculate IS gap
        is_gap = self.target.target_percentage - current_is
        
        # Determine bid adjustment based on target location
        if self.target.location == "absolute_top":
            # Need position 1 - be more aggressive
            position_factor = 1.5
            required_is = self.target.target_percentage * 1.2  # Need higher IS for pos 1
        elif self.target.location == "top_of_page":
            # Need positions 1-4
            position_factor = 1.2
            required_is = self.target.target_percentage
        else:  # anywhere
            # Any position OK
            position_factor = 1.0
            required_is = self.target.target_percentage
        
        # Calculate bid multiplier
        if is_gap > 20:
            # Far below target - aggressive increase
            self.bid_multiplier = 1.5 * position_factor
        elif is_gap > 10:
            # Below target - moderate increase
            self.bid_multiplier = 1.3 * position_factor
        elif is_gap > 5:
            # Slightly below - gentle increase
            self.bid_multiplier = 1.15 * position_factor
        elif is_gap < -20:
            # Far above target - reduce bids to save money
            self.bid_multiplier = 0.7
        elif is_gap < -10:
            # Above target - moderate decrease
            self.bid_multiplier = 0.85
        elif is_gap < -5:
            # Slightly above - gentle decrease
            self.bid_multiplier = 0.95
        else:
            # On target - maintain
            self.bid_multiplier = 1.0
        
        # Adjust for competition
        competition_multiplier = 0.9 + (competitor_density * 0.3)
        self.bid_multiplier *= competition_multiplier
        
        # Calculate final bid
        adjusted_bid = base_bid * self.bid_multiplier
        
        # Apply max CPC limit if set
        if self.target.max_cpc_bid_limit:
            adjusted_bid = min(adjusted_bid, self.target.max_cpc_bid_limit)
        
        return max(0.01, adjusted_bid)
    
    def get_bidding_explanation(self) -> Dict:
        """Educational explanation of current bidding decisions."""
        is_gap = self.target.target_percentage - self.current_is
        
        status = "on_target"
        if is_gap > 10:
            status = "below_target"
            action = "Increasing bids to gain more impressions"
        elif is_gap < -10:
            status = "above_target"
            action = "Decreasing bids to save budget while maintaining target"
        else:
            action = "Maintaining current bid levels"
        
        return {
            'target_is': self.target.target_percentage,
            'current_is': self.current_is,
            'gap': is_gap,
            'status': status,
            'bid_multiplier': self.bid_multiplier,
            'action': action,
            'target_location': self.target.location
        }


def render_location_targeting(config: Dict):
    """Render location targeting interface for campaign wizard."""
    st.write("Configure geographic targeting for your campaign.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Location selection
        location_type = st.radio(
            "Location targeting",
            ["All countries and territories", "Enter another location", "United States"],
            index=2 if "United States" in config.get('locations', []) else 0,
            label_visibility="collapsed"
        )
        
        if location_type == "Enter another location":
            locations = st.text_area(
                "Enter locations (one per line)",
                placeholder="New York, United States\nCalifornia, United States\nTexas, United States",
                help="Enter cities, states, countries, or postal codes",
                value='\n'.join(config.get('locations', []))
            )
            config['locations'] = [l.strip() for l in locations.split('\n') if l.strip()]
        elif location_type == "United States":
            config['locations'] = ["United States"]
        else:
            config['locations'] = ["All countries and territories"]
        
        # Location targeting type
        st.write("**Location targeting type:**")
        location_target_type = st.radio(
            "Target",
            ["Presence: People in or regularly in your targeted locations (recommended)", 
             "Presence or interest: People in, regularly in, or who've shown interest in your targeted locations",
             "Search interest: People searching for your targeted locations"],
            index=0,
            label_visibility="collapsed"
        )
        config['location_target_type'] = location_target_type.split(":")[0]
    
    with col2:
        # Location bid adjustments
        st.write("**Location bid adjustments:**")
        
        # Initialize geo bid adjustments if not exists
        if 'geo_bid_adjustments' not in config:
            config['geo_bid_adjustments'] = {}
        
        # Show adjustments for selected locations
        for location in config.get('locations', []):
            if location != "All countries and territories":
                adjustment = st.slider(
                    f"Bid adjustment for {location}",
                    min_value=-90,
                    max_value=900,
                    value=config['geo_bid_adjustments'].get(location, 0),
                    step=10,
                    format="%+d%%"
                )
                config['geo_bid_adjustments'][location] = adjustment
        
        # Exclude locations
        st.markdown("---")
        exclude_locations = st.checkbox("Exclude locations", value=config.get('exclude_locations', False))
        if exclude_locations:
            config['excluded_locations'] = st.text_area(
                "Locations to exclude",
                placeholder="Enter locations to exclude (one per line)",
                value=config.get('excluded_locations', '')
            )

def render_impression_share_bidding_setup(config: Dict):
    """
    UI for configuring Target Impression Share bidding strategy.
    """
    
    st.subheader("🎯 Target Impression Share Bidding")
    
    st.info("""
    **What is Target Impression Share?**
    
    Automatically sets bids to show your ad a certain percentage of the time.
    Great for brand awareness and visibility goals.
    """)
    
    # Target percentage
    col1, col2 = st.columns(2)
    
    with col1:
        target_is = st.slider(
            "Target Impression Share (%)",
            min_value=10,
            max_value=100,
            value=config.get('target_impression_share', 65),
            step=5,
            help="Percentage of eligible impressions you want to receive",
            key="target_is_pct"
        )
        config['target_impression_share'] = target_is
    
    with col2:
        target_location = st.selectbox(
            "Target Location",
            ["Anywhere on results page", "Top of results page", "Absolute top of results page"],
            index=0,
            help="Where you want to appear",
            key="target_is_location"
        )
        
        location_map = {
            "Anywhere on results page": "anywhere",
            "Top of results page": "top_of_page",
            "Absolute top of results page": "absolute_top"
        }
        config['target_location'] = location_map[target_location]
    
    # Max CPC bid limit
    st.write("**⚠️ Maximum CPC Bid Limit (Optional):**")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        use_max_cpc = st.checkbox(
            "Set a maximum CPC bid limit",
            value=config.get('has_max_cpc_limit', False),
            help="Prevents bids from going too high",
            key="use_max_cpc_limit"
        )
        config['has_max_cpc_limit'] = use_max_cpc
    
    with col2:
        if use_max_cpc:
            max_cpc = st.number_input(
                "Max CPC ($)",
                min_value=0.01,
                max_value=100.0,
                value=config.get('max_cpc_limit', 5.00),
                step=0.25,
                key="target_is_max_cpc"
            )
            config['max_cpc_limit'] = max_cpc
    
    # Predictions
    st.markdown("---")
    st.write("**📈 Expected Results:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Target IS", f"{target_is}%")
    
    with col2:
        # Estimate based on target location
        if config['target_location'] == 'absolute_top':
            estimated_position = 1.2
        elif config['target_location'] == 'top_of_page':
            estimated_position = 2.5
        else:
            estimated_position = 3.5
        
        st.metric("Estimated Avg Position", f"{estimated_position:.1f}")
    
    with col3:
        # Rough CPC estimate (higher IS = higher CPC)
        base_market_cpc = 1.50
        is_factor = (target_is / 50)  # Higher target = higher CPC
        location_factor = {
            'anywhere': 1.0,
            'top_of_page': 1.3,
            'absolute_top': 1.6
        }.get(config['target_location'], 1.0)
        
        estimated_cpc = base_market_cpc * is_factor * location_factor
        if config.get('has_max_cpc_limit'):
            estimated_cpc = min(estimated_cpc, config['max_cpc_limit'])
        
        st.metric("Estimated CPC", f"${estimated_cpc:.2f}")
    
    # Warnings
    if target_is > 80 and config['target_location'] == 'absolute_top':
        st.warning("⚠️ Targeting 80%+ IS at absolute top position can be very expensive. Consider lowering target or changing location.")
    
    if not config.get('has_max_cpc_limit'):
        st.info("💡 Consider setting a max CPC limit to prevent unexpectedly high costs")
    
    # Best practices - REPLACED EXPANDER WITH TOGGLE
    st.markdown("---")
    if st.checkbox("💡 Show Best Practices", value=False, key="show_is_best_practices"):
        st.markdown("""
        ### When to Use Target Impression Share
        
        **Good for:**
        - Brand awareness campaigns
        - Defending brand terms
        - Dominating specific keywords
        - Maintaining visibility
        
        **Not ideal for:**
        - Conversion-focused campaigns (use Target CPA instead)
        - Limited budgets (can spend quickly)
        - Testing new campaigns
        
        ### Recommended Settings
        
        **Brand Terms:**
        - Target: 80-95% IS
        - Location: Absolute Top
        - Max CPC: Set based on brand value
        
        **Competitive Keywords:**
        - Target: 50-65% IS
        - Location: Top of Page
        - Max CPC: 2-3x average CPC
        
        **General Visibility:**
        - Target: 50-70% IS
        - Location: Anywhere
        - Max CPC: 1.5x average CPC
        """)
