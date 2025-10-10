# /app/components/audience_manager.py
"""
Audience Targeting Component
Functional UI for managing audience segments and bid adjustments.
"""

import streamlit as st
from typing import Dict, List

# Predefined audience segments
AUDIENCE_LIBRARY = {
    "Your Data (Remarketing)": {
        "All Visitors": {"type": "remarketing", "size": "Large", "typical_cvr": 0.08},
        "Cart Abandoners": {"type": "remarketing", "size": "Medium", "typical_cvr": 0.15},
        "Past Purchasers": {"type": "remarketing", "size": "Medium", "typical_cvr": 0.12},
        "Newsletter Subscribers": {"type": "remarketing", "size": "Small", "typical_cvr": 0.10},
        "Engaged Visitors (30 days)": {"type": "remarketing", "size": "Medium", "typical_cvr": 0.09}
    },
    "In-Market": {
        "Consumer Electronics": {"type": "in_market", "size": "Large", "typical_cvr": 0.045},
        "Computers & Peripherals": {"type": "in_market", "size": "Large", "typical_cvr": 0.042},
        "Auto Buyers": {"type": "in_market", "size": "Large", "typical_cvr": 0.038},
        "Travel Intenders": {"type": "in_market", "size": "Large", "typical_cvr": 0.040},
        "Software Buyers": {"type": "in_market", "size": "Medium", "typical_cvr": 0.048}
    },
    "Affinity": {
        "Technology Enthusiasts": {"type": "affinity", "size": "Large", "typical_cvr": 0.025},
        "Sports Fans": {"type": "affinity", "size": "Large", "typical_cvr": 0.022},
        "Luxury Shoppers": {"type": "affinity", "size": "Medium", "typical_cvr": 0.028},
        "Travel Buffs": {"type": "affinity", "size": "Large", "typical_cvr": 0.024},
        "Business Professionals": {"type": "affinity", "size": "Medium", "typical_cvr": 0.035}
    },
    "Demographics": {
        "Age: 18-24": {"type": "demographic", "size": "Large", "typical_cvr": 0.025},
        "Age: 25-34": {"type": "demographic", "size": "Large", "typical_cvr": 0.038},
        "Age: 35-44": {"type": "demographic", "size": "Large", "typical_cvr": 0.042},
        "Age: 45-54": {"type": "demographic", "size": "Medium", "typical_cvr": 0.040},
        "Age: 55-64": {"type": "demographic", "size": "Medium", "typical_cvr": 0.035},
        "Household Income: Top 10%": {"type": "demographic", "size": "Small", "typical_cvr": 0.055},
        "Household Income: Top 20%": {"type": "demographic", "size": "Medium", "typical_cvr": 0.048},
        "Parents": {"type": "demographic", "size": "Large", "typical_cvr": 0.040}
    }
}

def render_audience_targeting(config: Dict, inside_expander: bool = False):
    """
    Render audience targeting interface.
    
    Features:
    - Select audience segments
    - Set bid adjustments per audience
    - Targeting vs Observation mode
    - Performance predictions
    
    Args:
        config: Campaign configuration dictionary
        inside_expander: Whether this is being rendered inside another expander
    """
    
    if not inside_expander:
        st.subheader("👥 Audience Targeting")
    
    st.write("""
    Target specific groups of users based on their interests, behaviors, or demographics.
    """)
    
    # Initialize
    if 'audience_segments' not in config:
        config['audience_segments'] = []
    if 'audience_bid_adjustments' not in config:
        config['audience_bid_adjustments'] = {}
    if 'audience_targeting_mode' not in config:
        config['audience_targeting_mode'] = 'observation'
    
    # Targeting mode
    st.write("**Targeting Mode:**")
    
    targeting_mode = st.radio(
        "Mode",
        ["Observation (Recommended)", "Targeting"],
        index=0 if config['audience_targeting_mode'] == 'observation' else 1,
        key="audience_mode",
        help="Observation = Monitor without restricting reach | Targeting = Only show to selected audiences"
    )
    
    config['audience_targeting_mode'] = 'observation' if 'Observation' in targeting_mode else 'targeting'
    
    if config['audience_targeting_mode'] == 'targeting':
        st.warning("⚠️ Targeting mode restricts your campaign to ONLY selected audiences. This reduces reach.")
    else:
        st.info("✅ Observation mode lets you adjust bids without restricting reach. Recommended for most campaigns.")
    
    st.markdown("---")
    
    # Audience selection by category
    st.write("**Select Audience Segments:**")
    
    tabs = st.tabs(["Remarketing", "In-Market", "Affinity", "Demographics"])
    
    for tab, (category, audiences) in zip(tabs, AUDIENCE_LIBRARY.items()):
        with tab:
            st.write(f"**{category}**")
            
            for audience_name, audience_data in audiences.items():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    is_selected = audience_name in config['audience_segments']
                    
                    selected = st.checkbox(
                        f"{audience_name}",
                        value=is_selected,
                        key=f"aud_{audience_name.replace(' ', '_')}_{category.replace(' ', '_')}"
                    )
                    
                    if selected and not is_selected:
                        config['audience_segments'].append(audience_name)
                    elif not selected and is_selected:
                        config['audience_segments'].remove(audience_name)
                    
                    st.caption(f"Size: {audience_data['size']} | Est. CVR: {audience_data['typical_cvr']*100:.1f}%")
                
                with col2:
                    if audience_name in config['audience_segments']:
                        bid_adj = st.slider(
                            "Bid Adj",
                            min_value=-90,
                            max_value=900,
                            value=config['audience_bid_adjustments'].get(audience_name, 0),
                            step=10,
                            format="%d%%",
                            key=f"aud_adj_{audience_name.replace(' ', '_')}",
                            label_visibility="collapsed"
                        )
                        config['audience_bid_adjustments'][audience_name] = bid_adj
                
                with col3:
                    if audience_name in config['audience_segments']:
                        multiplier = 1.0 + (config['audience_bid_adjustments'].get(audience_name, 0) / 100)
                        st.metric("", f"{multiplier:.1f}x", label_visibility="collapsed")
    
    # Summary
    st.markdown("---")
    if config['audience_segments']:
        st.success(f"✅ {len(config['audience_segments'])} audience segments selected")
        
        # Show selected with adjustments
        with st.expander("📋 Selected Audiences", expanded=True):
            for audience in config['audience_segments']:
                adjustment = config['audience_bid_adjustments'].get(audience, 0)
                if adjustment != 0:
                    st.write(f"• {audience}: {adjustment:+d}%")
                else:
                    st.write(f"• {audience}: No adjustment")
    else:
        st.info("No audiences selected. Ads will show to all users.")
    
    # Best practices
    if inside_expander:
        # When inside an expander, use a different approach to avoid nesting
        if st.button("💡 Show Best Practices", key="audience_best_practices"):
            st.session_state.show_audience_practices = not st.session_state.get('show_audience_practices', False)
        
        if st.session_state.get('show_audience_practices', False):
            st.markdown("""
            ### Bid Adjustment Guidelines
            
            **Remarketing (Your Data):**
            - All Visitors: +20% to +50% (familiar with brand)
            - Cart Abandoners: +50% to +100% (high intent)
            - Past Purchasers: +30% to +80% (proven buyers)
            
            **In-Market:**
            - Active buyers: +20% to +40%
            - Recent research: +10% to +30%
            
            **Affinity:**
            - Related interests: 0% to +20%
            - Broad interests: -10% to +10%
            
            **Demographics:**
            - High-value segments: +30% to +100%
            - Low-value segments: -30% to -50%
            
            ### Targeting vs Observation
            
            **Start with Observation:**
            1. Run campaign in observation mode
            2. Collect performance data by audience
            3. Identify high-performing segments
            4. Set bid adjustments based on data
            
            **Switch to Targeting when:**
            - You have clear winner segments
            - Budget is limited
            - Need to focus on specific demographics
            
            ### Example Strategy
            ```
            Mode: Observation
            - Past Purchasers: +80%
            - In-Market Electronics: +30%
            - Age 25-44: +20%
            - All other audiences: 0%
            
            After 30 days → Review data → Adjust
            ```
            """)
    else:
        # When not inside an expander, use the normal expander
        with st.expander("💡 Audience Targeting Best Practices", expanded=False):
            st.markdown("""
            ### Bid Adjustment Guidelines
            
            **Remarketing (Your Data):**
            - All Visitors: +20% to +50% (familiar with brand)
            - Cart Abandoners: +50% to +100% (high intent)
            - Past Purchasers: +30% to +80% (proven buyers)
            
            **In-Market:**
            - Active buyers: +20% to +40%
            - Recent research: +10% to +30%
            
            **Affinity:**
            - Related interests: 0% to +20%
            - Broad interests: -10% to +10%
            
            **Demographics:**
            - High-value segments: +30% to +100%
            - Low-value segments: -30% to -50%
            
            ### Targeting vs Observation
            
            **Start with Observation:**
            1. Run campaign in observation mode
            2. Collect performance data by audience
            3. Identify high-performing segments
            4. Set bid adjustments based on data
            
            **Switch to Targeting when:**
            - You have clear winner segments
            - Budget is limited
            - Need to focus on specific demographics
            
            ### Example Strategy
            ```
            Mode: Observation
            - Past Purchasers: +80%
            - In-Market Electronics: +30%
            - Age 25-44: +20%
            - All other audiences: 0%
            
            After 30 days → Review data → Adjust
            ```
            """)


def calculate_audience_impact(audience_segments: List[str], 
                             audience_adjustments: Dict[str, int],
                             base_cvr: float) -> Dict:
    """
    Calculate the impact of audience targeting on campaign performance.
    Educational function showing expected changes.
    """
    
    if not audience_segments:
        return {
            'estimated_cvr': base_cvr,
            'cvr_uplift': 0,
            'reach_impact': 'No change'
        }
    
    # Calculate weighted CVR based on audience segments
    total_cvr_boost = 0
    segment_count = 0
    
    for segment in audience_segments:
        # Find segment data
        for category, audiences in AUDIENCE_LIBRARY.items():
            if segment in audiences:
                audience_data = audiences[segment]
                
                # Get bid adjustment
                bid_adj = audience_adjustments.get(segment, 0)
                
                # Higher bid = more likely to show to this audience
                visibility_weight = 1.0 + (bid_adj / 100) * 0.5
                
                # Typical CVR for this audience
                segment_cvr = audience_data['typical_cvr']
                
                # Weighted contribution
                total_cvr_boost += segment_cvr * visibility_weight
                segment_count += 1
    
    if segment_count > 0:
        estimated_cvr = total_cvr_boost / segment_count
        cvr_uplift = ((estimated_cvr / base_cvr) - 1) * 100
    else:
        estimated_cvr = base_cvr
        cvr_uplift = 0
    
    return {
        'estimated_cvr': estimated_cvr,
        'cvr_uplift': cvr_uplift,
        'segment_count': segment_count
    }
