# /app/sidebar_stats.py
"""
Sidebar API Usage Statistics Display
Shows real-time token usage and limits for all APIs
"""

import streamlit as st
from services.usage_manager import get_usage_stats

def render_usage_stats():
    """Render API usage statistics in sidebar"""
    
    # Get usage statistics
    usage_stats = get_usage_stats()
    
    # API Usage Section
    st.markdown("---")
    st.subheader("🔋 API Usage")
    
    # Service Usage
    for service, stats in usage_stats.items():
        service_name = service.replace("_", " ").title()
        
        # Hourly Usage
        st.markdown(f"**{service_name} (Hourly)**")
        hourly_progress = stats["hourly_percent"] / 100
        hourly_color = "green" if hourly_progress < 0.7 else "orange" if hourly_progress < 0.9 else "red"
        
        st.progress(hourly_progress, text=f"{stats['hourly_used']}/{stats['hourly_limit']} tokens")
        
        # Daily Usage
        st.markdown(f"**{service_name} (Daily)**")
        daily_progress = stats["daily_percent"] / 100
        daily_color = "green" if daily_progress < 0.7 else "orange" if daily_progress < 0.9 else "red"
        
        st.progress(daily_progress, text=f"{stats['daily_used']}/{stats['daily_limit']} tokens")
        
        # Status indicators
        if hourly_progress > 0.8 or daily_progress > 0.8:
            st.warning(f"⚠️ {service_name} approaching limit!")
        elif hourly_progress >= 1.0 or daily_progress >= 1.0:
            st.error(f"🚫 {service_name} limit exceeded!")
        
        # Additional info
        if stats["total_requests"] > 0:
            st.caption(f"Total requests: {stats['total_requests']}")
        
        st.markdown("")  # Spacing
    
    # Reset Button
    st.markdown("---")
    st.subheader("🔄 Reset Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Reset All", help="Reset all API usage counters"):
            from services.usage_manager import force_reset
            force_reset()
            st.rerun()
    
    with col2:
        selected_service = st.selectbox(
            "Reset Service",
            ["All", "Gemini", "Google Ads", "Dialogflow"],
            help="Reset specific service counters"
        )
        
        if st.button("Reset Selected"):
            from services.usage_manager import force_reset
            if selected_service == "All":
                force_reset()
            else:
                service_key = selected_service.lower().replace(" ", "_")
                force_reset(service_key)
            st.rerun()
    
    # Usage Guidelines
    with st.expander("📋 Usage Guidelines"):
        st.markdown("""
        **API Limits:**
        - **Gemini**: 1,500 tokens/hour, 5,000/day
        - **Google Ads**: 300 tokens/hour, 1,000/day  
        - **Dialogflow**: 100 tokens/hour, 300/day
        
        **When Limits Are Exceeded:**
        - **Gemini**: Falls back to mock responses
        - **Google Ads**: Shows alert and stops
        - **Dialogflow**: Disables chatbot
        
        **Tips:**
        - Limits reset automatically every hour/day
        - Use mock data when possible to save tokens
        - Check usage before running large operations
        """)

def render_compact_usage():
    """Render compact usage display for limited sidebar space"""
    
    usage_stats = get_usage_stats()
    
    st.markdown("### 🔋 API Status")
    
    # Service status (compact)
    for service, stats in usage_stats.items():
        service_icon = {
            "gemini": "🤖",
            "google_ads": "📊", 
            "dialogflow": "💬"
        }.get(service, "🔧")
        
        daily_progress = stats["daily_percent"] / 100
        status_color = "🟢" if daily_progress < 0.7 else "🟡" if daily_progress < 0.9 else "🔴"
        
        st.write(f"{status_color} {service_icon} {service.replace('_', ' ').title()}: {stats['daily_used']}/{stats['daily_limit']}")
    
    # Quick reset
    if st.button("🔄 Reset All"):
        from services.usage_manager import force_reset
        force_reset()
        st.rerun()
