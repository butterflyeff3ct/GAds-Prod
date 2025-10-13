"""
Quota Display Component
Shows real-time API usage metrics to users
"""

import streamlit as st
from .quota_manager import get_quota_manager


def render_quota_metrics(location: str = "sidebar"):
    """
    Render quota usage metrics
    
    Args:
        location: 'sidebar' or 'main' - where to display
    """
    quota_mgr = get_quota_manager()
    summary = quota_mgr.get_quota_summary()
    
    if location == "sidebar":
        _render_sidebar_quotas(summary)
    else:
        _render_main_quotas(summary)


def _render_sidebar_quotas(summary: dict):
    """Render compact quota display for sidebar"""
    
    st.markdown("---")
    st.subheader("📊 API Usage")
    
    # Gemini Tokens
    gemini = summary['gemini']
    
    st.write("**🤖 Gemini Tokens**")
    st.progress(
        min(gemini['percentage'] / 100, 1.0),
        text=f"{gemini['used']:,}/{gemini['limit']:,}"
    )
    
    if gemini['exceeded']:
        st.error("❌ Quota exceeded - Using mock data")
    elif gemini['remaining'] < 1000:
        st.warning(f"⚠️ {gemini['remaining']:,} remaining")
    else:
        st.caption(f"✅ {gemini['remaining']:,} remaining")
    
    st.markdown("")  # Spacing
    
    # Google Ads Operations
    ads = summary['google_ads']
    
    st.write("**🔍 Google Ads Operations**")
    st.progress(
        min(ads['percentage'] / 100, 1.0),
        text=f"{ads['used']}/{ads['limit']}"
    )
    
    if ads['exceeded']:
        st.error("❌ Quota exceeded - Using mock data")
    elif ads['remaining'] <= 2:
        st.warning(f"⚠️ {ads['remaining']} remaining")
    else:
        st.caption(f"✅ {ads['remaining']} remaining")


def _render_main_quotas(summary: dict):
    """Render detailed quota display for main content area"""
    
    st.subheader("📊 API Usage Quotas")
    
    col1, col2 = st.columns(2)
    
    # Gemini Tokens
    with col1:
        gemini = summary['gemini']
        
        st.markdown("### 🤖 Gemini Tokens")
        
        # Main metric
        st.metric(
            "Tokens Used",
            f"{gemini['used']:,} / {gemini['limit']:,}",
            delta=f"-{gemini['remaining']:,} remaining" if not gemini['exceeded'] else "Exceeded",
            delta_color="inverse"
        )
        
        # Progress bar
        st.progress(
            min(gemini['percentage'] / 100, 1.0),
            text=f"{gemini['percentage']:.1f}% used"
        )
        
        # Status message
        if gemini['exceeded']:
            st.error("❌ **Quota Exceeded**")
            st.info("🔄 Using mock data for Gemini operations")
        elif gemini['remaining'] < 1000:
            st.warning(f"⚠️ **Low Quota:** {gemini['remaining']:,} tokens remaining")
        else:
            st.success(f"✅ **{gemini['remaining']:,}** tokens available")
        
        # What uses tokens
        with st.expander("ℹ️ What uses Gemini tokens?"):
            st.write("""
            **Gemini API is used for:**
            - Keyword generation
            - Ad copy generation
            - Campaign insights
            - AI-powered recommendations
            
            **Token usage examples:**
            - Keyword generation: ~500-1000 tokens
            - Ad copy generation: ~300-500 tokens
            - Campaign insights: ~200-400 tokens
            """)
    
    # Google Ads Operations
    with col2:
        ads = summary['google_ads']
        
        st.markdown("### 🔍 Google Ads Operations")
        
        # Main metric
        st.metric(
            "Operations Used",
            f"{ads['used']} / {ads['limit']}",
            delta=f"-{ads['remaining']} remaining" if not ads['exceeded'] else "Exceeded",
            delta_color="inverse"
        )
        
        # Progress bar
        st.progress(
            min(ads['percentage'] / 100, 1.0),
            text=f"{ads['percentage']:.1f}% used"
        )
        
        # Status message
        if ads['exceeded']:
            st.error("❌ **Quota Exceeded**")
            st.info("🔄 Using mock data for Google Ads operations")
        elif ads['remaining'] <= 2:
            st.warning(f"⚠️ **Low Quota:** {ads['remaining']} operations remaining")
        else:
            st.success(f"✅ **{ads['remaining']}** operations available")
        
        # What counts as operation
        with st.expander("ℹ️ What counts as an operation?"):
            st.write("""
            **Google Ads API operations:**
            - Keyword data requests
            - Search volume queries
            - Competition analysis
            - Location targeting data
            
            **Each API call = 1 operation**
            
            Limit helps control API costs.
            """)
    
    # Overall status
    st.markdown("---")
    
    if gemini['exceeded'] and ads['exceeded']:
        st.error("⚠️ **Both quotas exceeded** - All operations using mock data")
        st.info("💡 **Tip:** Mock data is great for learning and testing without API costs!")
    elif gemini['exceeded'] or ads['exceeded']:
        st.warning("⚠️ **One quota exceeded** - Partial mock data usage")
    else:
        st.success("✅ **All quotas active** - Using real API data")


def render_quota_warning_banner():
    """
    Render warning banner when quotas are low or exceeded
    Show at top of page
    """
    quota_mgr = get_quota_manager()
    summary = quota_mgr.get_quota_summary()
    
    gemini = summary['gemini']
    ads = summary['google_ads']
    
    # Check if we should show warning
    show_warning = False
    warning_message = []
    
    if gemini['exceeded']:
        show_warning = True
        warning_message.append("🤖 **Gemini quota exceeded** - using mock data")
    elif gemini['remaining'] < 1000:
        show_warning = True
        warning_message.append(f"🤖 **Gemini quota low:** {gemini['remaining']:,} tokens remaining")
    
    if ads['exceeded']:
        show_warning = True
        warning_message.append("🔍 **Google Ads quota exceeded** - using mock data")
    elif ads['remaining'] <= 2:
        show_warning = True
        warning_message.append(f"🔍 **Google Ads quota low:** {ads['remaining']} operations remaining")
    
    # Display warning if needed
    if show_warning:
        if gemini['exceeded'] or ads['exceeded']:
            st.error(" | ".join(warning_message))
            st.info("💡 **No worries!** The simulator works great with mock data. You can still learn and test campaigns without API access.")
        else:
            st.warning(" | ".join(warning_message))


def render_quota_badge(quota_type: str = "both"):
    """
    Render small quota badge
    
    Args:
        quota_type: 'gemini', 'google_ads', or 'both'
    """
    quota_mgr = get_quota_manager()
    
    if quota_type in ['gemini', 'both']:
        used, limit = quota_mgr.get_gemini_usage()
        exceeded = used >= limit
        
        if exceeded:
            st.error(f"🤖 Gemini: {used:,}/{limit:,} ❌")
        else:
            st.success(f"🤖 Gemini: {used:,}/{limit:,}")
    
    if quota_type in ['google_ads', 'both']:
        used, limit = quota_mgr.get_google_ads_usage()
        exceeded = used >= limit
        
        if exceeded:
            st.error(f"🔍 Ads: {used}/{limit} ❌")
        else:
            st.success(f"🔍 Ads: {used}/{limit}")
