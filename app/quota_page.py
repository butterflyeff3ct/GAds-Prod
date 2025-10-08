# app/quota_page.py
"""
Quota Dashboard Page
Shows user their API usage, limits, and activity history.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from auth.quota_manager import QuotaManager
from auth.user_activity import UserActivityLogger
from auth.session_manager import SessionManager
from database.db_manager import get_database_manager
from datetime import datetime

def render_quota_dashboard():
    """
    Render user's quota and usage dashboard.
    Shows API limits, current usage, and activity history.
    """
    
    st.header("📊 Your Usage & Quotas")
    
    # Get current user
    user_email = SessionManager.get_user_email()
    if not user_email:
        st.error("Not authenticated")
        return
    
    quota_manager = QuotaManager()
    quota_status = quota_manager.get_user_quota_status(user_email)
    
    # ========== QUOTA OVERVIEW ==========
    st.subheader("API Quotas (Hourly Limits)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create quota cards
        for api_data in quota_status.get('quotas', []):
            with st.container():
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    st.write(f"**{api_data['name']}**")
                
                with col_b:
                    usage_text = f"{api_data['usage']}/{api_data['limit']}"
                    st.write(usage_text)
                
                with col_c:
                    # Status indicator
                    if api_data['status'] == 'exceeded':
                        st.error("🚫 Exceeded")
                    elif api_data['status'] == 'warning':
                        st.warning("⚠️ High")
                    else:
                        st.success("✅ OK")
                
                # Progress bar
                progress_color = (
                    'red' if api_data['status'] == 'exceeded' else
                    'orange' if api_data['status'] == 'warning' else
                    'green'
                )
                
                st.progress(
                    min(api_data['percentage'] / 100, 1.0),
                    text=f"{api_data['percentage']:.0f}% used"
                )
    
    with col2:
        # Reset countdown
        reset_minutes = quota_status.get('reset_in_minutes', 0)
        st.metric(
            "⏰ Quota Resets In",
            f"{reset_minutes} min",
            help="All quotas reset every hour"
        )
        
        # Session time
        session_time = SessionManager.get_session_time_remaining()
        st.metric(
            "🕐 Session Expires In",
            f"{session_time} min",
            help="Your session will expire after 2 hours of inactivity"
        )
    
    # ========== USAGE CHART ==========
    st.markdown("---")
    st.subheader("📈 Recent Activity")
    
    # Get activities
    activities = UserActivityLogger.get_user_activities(user_email, limit=20)
    
    if activities:
        # Create timeline
        activity_df = pd.DataFrame(activities)
        activity_df['timestamp'] = pd.to_datetime(activity_df['timestamp'])
        
        # Count by type
        activity_counts = activity_df['activity_type'].value_counts()
        
        fig = go.Figure(data=[
            go.Bar(
                x=activity_counts.index,
                y=activity_counts.values,
                marker_color='#4285F4'
            )
        ])
        
        fig.update_layout(
            title='Activity Breakdown (Last 20 Actions)',
            xaxis_title='Activity Type',
            yaxis_title='Count',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Activity list
        st.write("**Recent Actions:**")
        for i, activity in enumerate(activities[:10]):
            time_str = datetime.fromisoformat(activity['timestamp']).strftime('%H:%M:%S')
            st.caption(f"{time_str} - {activity['activity_name']}")
    else:
        st.info("No recent activity")
    
    # ========== EXPORT OPTIONS ==========
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Activity Log", use_container_width=True):
            activity_json = UserActivityLogger.export_activities(user_email)
            st.download_button(
                label="Download JSON",
                data=activity_json,
                file_name=f"activity_log_{user_email}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # ========== QUOTA GUIDELINES ==========
    with st.expander("ℹ️ Understanding Quotas", expanded=False):
        st.markdown("""
        ### Quota System
        
        **Why Quotas?**
        - Ensure fair access for all users
        - Prevent API abuse
        - Manage infrastructure costs
        - Educational use focus
        
        **Hourly Limits:**
        - Google Ads API: 10 calls/hour
        - Gemini API: 20 calls/hour
        - Keyword Planner: 15 calls/hour
        - Simulations: 5/hour
        
        **What Counts:**
        - ✅ Running simulations
        - ✅ Keyword research with API
        - ✅ AI-generated content
        - ❌ Viewing reports (free)
        - ❌ Campaign setup (free)
        - ❌ Using mock data (free)
        
        **Tips to Stay Within Limits:**
        1. Use mock data for learning/testing
        2. Plan campaigns before running simulations
        3. Export data to analyze offline
        4. Use the Planner page efficiently
        
        **Need More Quota?**
        - Quotas reset every hour automatically
        - Educational users get priority during off-peak hours
        - Contact admin for custom quotas
        """)
