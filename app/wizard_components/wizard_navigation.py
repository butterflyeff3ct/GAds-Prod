"""
Campaign Wizard Step Navigation Helper
Renders the left sidebar with step-by-step navigation
"""

import streamlit as st


def render_wizard_step_sidebar(current_step: int, total_steps: int):
    """
    Render the wizard step navigation sidebar
    Mimics Google Ads campaign creation flow with free navigation
    
    Args:
        current_step: Current step number (1-9)
        total_steps: Total number of steps
    """
    
    # Initialize visited steps tracker
    if 'wizard_visited_steps' not in st.session_state:
        st.session_state.wizard_visited_steps = set()
    
    # Add current step to visited steps
    st.session_state.wizard_visited_steps.add(current_step)
    
    # Track the highest step reached
    if 'wizard_max_step' not in st.session_state:
        st.session_state.wizard_max_step = 1
    
    # Update max step if we've gone further
    if current_step > st.session_state.wizard_max_step:
        st.session_state.wizard_max_step = current_step
    
    # Define all steps with icons and names
    steps = [
        {"number": 1, "name": "Search", "icon": "🔍"},
        {"number": 2, "name": "Bidding", "icon": "💰"},
        {"number": 3, "name": "Campaign settings", "icon": "⚙️"},
        {"number": 4, "name": "AI Max", "icon": "🤖"},
        {"number": 5, "name": "Keyword and asset\ngeneration", "icon": "🔑"},
        {"number": 6, "name": "Ad groups", "icon": "📁"},
        {"number": 7, "name": "Budget", "icon": "💵"},
        {"number": 8, "name": "Review", "icon": "👁️"},
        {"number": 9, "name": "Launch", "icon": "🚀"},
    ]
    
    # Render step navigation in sidebar
    with st.sidebar:
        st.markdown("### Campaign Setup")
        st.caption(f"Step {current_step} of {total_steps}")
        
        st.markdown("---")
        
        # Render each step
        for step in steps:
            step_num = step["number"]
            step_name = step["name"]
            step_icon = step["icon"]
            
            # Determine if this step is clickable
            is_visited = step_num in st.session_state.wizard_visited_steps
            is_current = step_num == current_step
            
            # Determine step status and appearance
            if is_current:
                # Current step - highlighted, not clickable
                status_icon = "▶️"
                button_style = "primary"
                disabled = True
                clickable = False
            elif is_visited:
                # Previously visited step - can click to navigate
                if step_num < current_step:
                    status_icon = "✅"  # Completed (before current)
                else:
                    status_icon = "✏️"  # Visited but after current (user went back)
                button_style = "secondary"
                disabled = False
                clickable = True
            else:
                # Not yet visited - disabled
                status_icon = "⭕"
                button_style = "secondary"
                disabled = True
                clickable = False
            
            # Render step
            if is_current:
                # Current step - show as highlighted box (no button)
                st.markdown(
                    f"""
                    <div style="background-color: #0d47a1; padding: 12px; border-radius: 8px; border-left: 4px solid #1a73e8; margin-bottom: 8px;">
                        <strong>{status_icon} {step_num}. {step_name}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Other steps - show as button
                if st.button(
                    f"{status_icon} {step_num}. {step_name}",
                    key=f"wizard_nav_step_{step_num}",
                    use_container_width=True,
                    type=button_style,
                    disabled=disabled,
                    help="Click to navigate to this step" if clickable else "Complete previous steps first"
                ):
                    # Navigate to selected step
                    st.session_state.campaign_step = step_num
                    # Reset cancel confirmation when navigating
                    if 'wizard_confirm_cancel' in st.session_state:
                        st.session_state.wizard_confirm_cancel = False
                    st.rerun()
            
            # Add small spacing between steps
            st.markdown("")
        
        st.markdown("---")
        
        # Cancel section with inline confirmation
        if not st.session_state.get('wizard_confirm_cancel', False):
            # First state - show cancel button
            if st.button("❌ Cancel Campaign", use_container_width=True, type="secondary", key="cancel_campaign_btn"):
                st.session_state.wizard_confirm_cancel = True
                st.rerun()
        else:
            # Confirmation state - show warning and confirm/back buttons
            st.warning("⚠️ **Are you sure?**")
            st.caption("All progress will be lost")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Cancel", use_container_width=True, type="primary", key="confirm_cancel"):
                    # Confirmed - exit wizard and reset tracking
                    st.session_state.campaign_step = 0
                    st.session_state.wizard_confirm_cancel = False
                    reset_wizard_navigation()
                    st.rerun()
            
            with col2:
                if st.button("↩️ Go Back", use_container_width=True, key="cancel_cancel"):
                    # User changed their mind
                    st.session_state.wizard_confirm_cancel = False
                    st.rerun()


def reset_wizard_navigation():
    """
    Reset wizard navigation state
    Call this when exiting the wizard or starting fresh
    """
    if 'wizard_visited_steps' in st.session_state:
        st.session_state.wizard_visited_steps = set()
    if 'wizard_max_step' in st.session_state:
        st.session_state.wizard_max_step = 1
    if 'wizard_confirm_cancel' in st.session_state:
        st.session_state.wizard_confirm_cancel = False
