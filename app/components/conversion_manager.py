# /app/components/conversion_manager.py
"""
Conversion Actions Manager
Manage multiple conversion types with different values and attribution windows.
"""

import streamlit as st
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ConversionAction:
    """Represents a conversion action."""
    name: str
    category: str  # Purchase, Lead, Signup, PageView, etc.
    value: float
    count_type: str  # "one" or "every"
    attribution_window: int  # days
    
CONVERSION_CATEGORIES = {
    "Purchase": {
        "icon": "🛒",
        "default_value": 100.0,
        "count": "one",
        "window": 30
    },
    "Lead": {
        "icon": "📝",
        "default_value": 50.0,
        "count": "one",
        "window": 90
    },
    "Sign-up": {
        "icon": "✍️",
        "default_value": 25.0,
        "count": "one",
        "window": 30
    },
    "Phone Call": {
        "icon": "📞",
        "default_value": 40.0,
        "count": "one",
        "window": 30
    },
    "Add to Cart": {
        "icon": "🛍️",
        "default_value": 0.0,
        "count": "every",
        "window": 7
    },
    "Page View": {
        "icon": "👁️",
        "default_value": 0.0,
        "count": "every",
        "window": 1
    },
    "Download": {
        "icon": "⬇️",
        "default_value": 15.0,
        "count": "one",
        "window": 30
    }
}

def render_conversion_actions(config: Dict):
    """
    Render conversion actions management interface.
    
    Features:
    - Create multiple conversion types
    - Set values for each
    - Set attribution windows
    - Primary conversion selection
    """
    
    st.subheader("🎯 Conversion Actions")
    
    st.write("""
    Define what actions you want to track and optimize for.
    Different actions can have different values and counting methods.
    """)
    
    # Initialize
    if 'conversion_actions' not in config:
        config['conversion_actions'] = []
    if 'primary_conversion' not in config:
        config['primary_conversion'] = None
    
    # Quick add from templates
    st.write("**Quick Add from Template:**")
    
    cols = st.columns(4)
    for i, (category, settings) in enumerate(list(CONVERSION_CATEGORIES.items())[:4]):
        with cols[i]:
            icon = settings['icon']
            if st.button(f"{icon} {category}", use_container_width=True, key=f"add_conv_{category}"):
                # Check if already exists
                existing_names = [ca.get('name') for ca in config['conversion_actions']]
                if category not in existing_names:
                    config['conversion_actions'].append({
                        'name': category,
                        'category': category,
                        'value': settings['default_value'],
                        'count_type': settings['count'],
                        'attribution_window': settings['window'],
                        'enabled': True
                    })
                    st.rerun()
    
    st.markdown("---")
    
    # Display existing conversion actions
    if config['conversion_actions']:
        st.write("**Configured Conversion Actions:**")
        
        for i, conv_action in enumerate(config['conversion_actions']):
            with st.expander(f"{CONVERSION_CATEGORIES.get(conv_action['category'], {}).get('icon', '🎯')} {conv_action['name']}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Conversion name
                    conv_action['name'] = st.text_input(
                        "Conversion Name",
                        value=conv_action.get('name', ''),
                        key=f"conv_name_{i}"
                    )
                    
                    # Category
                    conv_action['category'] = st.selectbox(
                        "Category",
                        options=list(CONVERSION_CATEGORIES.keys()),
                        index=list(CONVERSION_CATEGORIES.keys()).index(conv_action.get('category', 'Purchase')) if conv_action.get('category') in CONVERSION_CATEGORIES else 0,
                        key=f"conv_cat_{i}"
                    )
                    
                    # Value
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        conv_action['value'] = st.number_input(
                            "Value ($)",
                            min_value=0.0,
                            value=float(conv_action.get('value', 0.0)),
                            step=5.0,
                            key=f"conv_value_{i}",
                            help="How much is this conversion worth to your business?"
                        )
                    
                    with col_b:
                        conv_action['count_type'] = st.selectbox(
                            "Count",
                            ["one", "every"],
                            index=0 if conv_action.get('count_type', 'one') == 'one' else 1,
                            key=f"conv_count_{i}",
                            help="One = Count once per click | Every = Count all conversions"
                        )
                    
                    with col_c:
                        conv_action['attribution_window'] = st.number_input(
                            "Window (days)",
                            min_value=1,
                            max_value=90,
                            value=int(conv_action.get('attribution_window', 30)),
                            key=f"conv_window_{i}",
                            help="How many days after ad click to count conversions"
                        )
                
                with col2:
                    # Primary conversion toggle
                    is_primary = st.checkbox(
                        "Primary",
                        value=config.get('primary_conversion') == conv_action['name'],
                        key=f"conv_primary_{i}",
                        help="Primary conversion used for bidding strategies"
                    )
                    
                    if is_primary:
                        config['primary_conversion'] = conv_action['name']
                    
                    # Enable/disable
                    conv_action['enabled'] = st.toggle(
                        "Enabled",
                        value=conv_action.get('enabled', True),
                        key=f"conv_enabled_{i}"
                    )
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"conv_delete_{i}"):
                        config['conversion_actions'].pop(i)
                        st.rerun()
        
        # Summary
        st.markdown("---")
        enabled_count = sum(1 for ca in config['conversion_actions'] if ca.get('enabled', True))
        total_value = sum(ca.get('value', 0) for ca in config['conversion_actions'] if ca.get('enabled', True))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Conversions", enabled_count)
        with col2:
            st.metric("Total Value", f"${total_value:.2f}")
        with col3:
            primary = config.get('primary_conversion', 'None')
            st.metric("Primary", primary)
    
    else:
        st.info("No conversion actions configured. Add at least one to track conversions.")
    
    # Custom conversion action
    st.markdown("---")
    with st.expander("➕ Add Custom Conversion Action", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            custom_name = st.text_input(
                "Conversion Name",
                placeholder="Newsletter Signup",
                key="custom_conv_name"
            )
        
        with col2:
            custom_category = st.selectbox(
                "Category",
                options=list(CONVERSION_CATEGORIES.keys()),
                key="custom_conv_category"
            )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            custom_value = st.number_input(
                "Value ($)",
                min_value=0.0,
                value=10.0,
                step=5.0,
                key="custom_conv_value"
            )
        
        with col2:
            custom_count = st.selectbox(
                "Count Type",
                ["one", "every"],
                key="custom_conv_count"
            )
        
        with col3:
            custom_window = st.number_input(
                "Attribution Window (days)",
                min_value=1,
                max_value=90,
                value=30,
                key="custom_conv_window"
            )
        
        if st.button("Add Conversion Action", key="add_custom_conv"):
            if custom_name:
                config['conversion_actions'].append({
                    'name': custom_name,
                    'category': custom_category,
                    'value': custom_value,
                    'count_type': custom_count,
                    'attribution_window': custom_window,
                    'enabled': True
                })
                st.success(f"Added '{custom_name}' conversion action!")
                st.rerun()
            else:
                st.error("Please enter a conversion name")
    
    # Educational info
    with st.expander("📚 Understanding Conversion Actions", expanded=False):
        st.markdown("""
        ### Key Concepts
        
        **Conversion Value:**
        - Set based on actual business value
        - Purchase = product price
        - Lead = estimated lifetime value
        - Signup = acquisition cost saved
        
        **Count Type:**
        - **One:** Only count the first conversion per click
          - Use for: Purchases, Signups, Leads
        - **Every:** Count all conversions
          - Use for: Page views, Add to carts, Downloads
        
        **Attribution Window:**
        - How long after a click to count conversions
        - Longer for considered purchases (30-90 days)
        - Shorter for impulse buys (7-14 days)
        - B2B often uses 90 days
        
        ### Primary Conversion
        
        The primary conversion is used for:
        - Target CPA bidding
        - Target ROAS bidding
        - Optimization focus
        
        **Best Practice:** Set your most valuable conversion as primary
        
        ### Example Setup (E-commerce)
        
        ```
        1. Purchase (Primary)
           Value: $75 average
           Count: One
           Window: 30 days
           
        2. Add to Cart
           Value: $0
           Count: Every
           Window: 7 days
           
        3. Newsletter Signup
           Value: $5
           Count: One
           Window: 30 days
        ```
        """)
