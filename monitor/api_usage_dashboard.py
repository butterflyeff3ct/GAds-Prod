# /monitor/api_usage_dashboard.py
"""
Real-Time API Usage Dashboard for Streamlit
Displays live token/operation/call counts with auto-refresh
"""

import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

from .google_ads_monitor import get_google_ads_usage
from .gemini_monitor import get_gemini_usage
from .dialogflow_monitor import get_dialogflow_usage
from .usage_logger import get_usage_logger

def render_api_usage_dashboard(refresh_interval: int = 60):
    """Render the real-time API usage dashboard in sidebar"""
    
    st.markdown("---")
    st.subheader("🧠 API Usage Monitor (Real-Time)")
    
    # Auto-refresh placeholder
    placeholder = st.empty()
    
    # Get current usage data
    with st.spinner("Fetching API usage data..."):
        try:
            # Get usage data from all monitors
            google_ads_data = get_google_ads_usage()
            gemini_data = get_gemini_usage()
            dialogflow_data = get_dialogflow_usage()
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="📊 Google Ads Ops",
                    value=f"{google_ads_data.get('logged_operations_today', 0)}",
                    delta=f"{google_ads_data.get('logged_operations_last_hour', 0)} last hour"
                )
                
                # Show monitoring status
                if google_ads_data.get('monitoring_available'):
                    st.caption("🟢 Live monitoring")
                else:
                    st.caption("🟡 Log-based")
            
            with col2:
                st.metric(
                    label="🤖 Gemini Tokens",
                    value=f"{gemini_data.get('tokens_today', 0):,}",
                    delta=f"{gemini_data.get('tokens_last_hour', 0):,} last hour"
                )
                
                # Show quota status
                daily_percent = gemini_data.get('daily_percent', 0)
                if daily_percent > 80:
                    st.caption("🔴 High usage")
                elif daily_percent > 50:
                    st.caption("🟡 Medium usage")
                else:
                    st.caption("🟢 Normal usage")
            
            with col3:
                st.metric(
                    label="💬 Dialogflow Calls",
                    value=f"{dialogflow_data.get('logged_calls_today', 0)}",
                    delta=f"{dialogflow_data.get('logged_calls_last_hour', 0)} last hour"
                )
                
                # Show monitoring status
                if dialogflow_data.get('monitoring_available'):
                    st.caption("🟢 Live monitoring")
                else:
                    st.caption("🟡 Log-based")
            
            # Detailed breakdown in expandable section
            with st.expander("📈 Detailed Usage Breakdown"):
                render_detailed_usage(google_ads_data, gemini_data, dialogflow_data)
            
            # API Health Status
            with st.expander("🏥 API Health Status"):
                render_health_status(google_ads_data, gemini_data, dialogflow_data)
            
            # Last updated timestamp
            last_updated = datetime.now().strftime("%H:%M:%S")
            st.caption(f"Last updated: {last_updated}")
            
            # Auto-refresh button
            if st.button("🔄 Refresh Now", key="refresh_api_usage"):
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error fetching API usage data: {e}")
            st.info("💡 API monitoring will use cached data when available")

def render_detailed_usage(google_ads_data: Dict, gemini_data: Dict, dialogflow_data: Dict):
    """Render detailed usage breakdown"""
    
    # Create usage summary table
    usage_data = [
        {
            "API": "Google Ads",
            "Operations (Today)": google_ads_data.get('logged_operations_today', 0),
            "Operations (Hour)": google_ads_data.get('logged_operations_last_hour', 0),
            "Avg Response (ms)": f"{google_ads_data.get('avg_response_time_ms', 0):.1f}",
            "Status": "🟢 Active" if google_ads_data.get('monitoring_available') else "🟡 Log-based"
        },
        {
            "API": "Gemini AI",
            "Tokens (Today)": f"{gemini_data.get('tokens_today', 0):,}",
            "Tokens (Hour)": f"{gemini_data.get('tokens_last_hour', 0):,}",
            "Quota Usage": f"{gemini_data.get('daily_percent', 0):.1f}%",
            "Status": "🟢 Active" if gemini_data.get('api_available') else "🔴 Unavailable"
        },
        {
            "API": "Dialogflow",
            "Calls (Today)": dialogflow_data.get('logged_calls_today', 0),
            "Calls (Hour)": dialogflow_data.get('logged_calls_last_hour', 0),
            "Avg Response (ms)": f"{dialogflow_data.get('avg_response_time_ms', 0):.1f}",
            "Status": "🟢 Active" if dialogflow_data.get('dialogflow_available') else "🔴 Unavailable"
        }
    ]
    
    df = pd.DataFrame(usage_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Show quota progress bars
    st.markdown("**Quota Usage:**")
    
    # Gemini quota
    gemini_daily_percent = gemini_data.get('daily_percent', 0)
    st.progress(gemini_daily_percent / 100, text=f"Gemini Daily: {gemini_daily_percent:.1f}% ({gemini_data.get('daily_used', 0):,}/{gemini_data.get('daily_quota', 5000):,} tokens)")
    
    # Dialogflow quota
    dialogflow_daily_percent = dialogflow_data.get('daily_percent', 0)
    st.progress(dialogflow_daily_percent / 100, text=f"Dialogflow Daily: {dialogflow_daily_percent:.1f}% ({dialogflow_data.get('daily_used', 0)}/{dialogflow_data.get('daily_quota', 300)} calls)")

def render_health_status(google_ads_data: Dict, gemini_data: Dict, dialogflow_data: Dict):
    """Render API health status"""
    
    logger = get_usage_logger()
    health_stats = logger.get_api_health_stats()
    
    # Overall health indicators
    st.markdown("**Overall API Health:**")
    
    # Success rates
    success_rates = health_stats.get('success_rates', {})
    
    for api_name, stats in success_rates.items():
        success_rate = stats.get('success_rate', 0)
        total_calls = stats.get('total_calls', 0)
        avg_response_time = stats.get('avg_response_time_ms', 0)
        
        if success_rate >= 95:
            status_icon = "🟢"
        elif success_rate >= 85:
            status_icon = "🟡"
        else:
            status_icon = "🔴"
        
        st.write(f"{status_icon} **{api_name}**: {success_rate:.1f}% success rate ({total_calls} calls, {avg_response_time:.0f}ms avg)")
    
    # Recent errors
    recent_errors = health_stats.get('recent_errors', [])
    if recent_errors:
        st.markdown("**Recent Errors:**")
        for error in recent_errors[:5]:  # Show last 5 errors
            st.error(f"**{error['api']}**: {error['error']} ({error['timestamp']})")
    else:
        st.success("✅ No recent errors detected")

def render_historical_trends(days: int = 7):
    """Render historical usage trends"""
    
    logger = get_usage_logger()
    
    st.markdown("---")
    st.subheader("📊 Historical Trends")
    
    # Get historical data for each API
    apis = ["Google Ads", "Gemini", "Dialogflow"]
    
    for api in apis:
        trends = logger.get_historical_trends(api, days)
        
        if trends:
            st.markdown(f"**{api} Usage (Last {days} days):**")
            
            # Create trend data
            dates = [trend['date'] for trend in trends]
            tokens = [trend['total_tokens'] for trend in trends]
            operations = [trend['total_operations'] for trend in trends]
            calls = [trend['total_calls'] for trend in trends]
            
            # Display as metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tokens", f"{sum(tokens):,}")
            with col2:
                st.metric("Total Operations", f"{sum(operations):,}")
            with col3:
                st.metric("Total Calls", f"{sum(calls):,}")
        else:
            st.info(f"No historical data available for {api}")

def render_compact_usage():
    """Render compact usage display for limited sidebar space"""
    
    try:
        # Get usage data
        google_ads_data = get_google_ads_usage()
        gemini_data = get_gemini_usage()
        dialogflow_data = get_dialogflow_usage()
        
        st.markdown("### 🧠 API Monitor")
        
        # Compact metrics
        st.write(f"📊 **Google Ads**: {google_ads_data.get('logged_operations_today', 0)} ops")
        st.write(f"🤖 **Gemini**: {gemini_data.get('tokens_today', 0):,} tokens")
        st.write(f"💬 **Dialogflow**: {dialogflow_data.get('logged_calls_today', 0)} calls")
        
        # Quick refresh
        if st.button("🔄", help="Refresh API usage"):
            st.rerun()
            
    except Exception as e:
        st.warning("⚠️ API monitoring unavailable")

# Auto-refresh functionality (optional)
def enable_auto_refresh(interval_seconds: int = 60):
    """Enable auto-refresh for the dashboard"""
    try:
        import streamlit_autorefresh as sar
        sar.st_autorefresh(interval=interval_seconds * 1000, key="api_usage_monitor")
    except ImportError:
        st.info("💡 Install `streamlit-autorefresh` for automatic updates")
    except Exception as e:
        st.warning(f"⚠️ Auto-refresh not available: {e}")
