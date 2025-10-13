"""
Forecast Display Component
Shows keyword plan forecast metrics in campaign wizard and dashboard
"""

import streamlit as st
from typing import Dict


def render_forecast_metrics(forecast: Dict, show_details: bool = True):
    """
    Render forecast metrics in a clean, professional layout
    
    Args:
        forecast: Dictionary with forecast data
        show_details: Whether to show detailed breakdown
    """
    
    # Check if mock data
    is_mock = forecast.get('is_mock', False)
    
    # Header
    if is_mock:
        st.info("📊 **Performance Forecast** (Educational Mock Data)")
    else:
        st.success("📊 **Performance Forecast** (Google Ads API Data)")
    
    st.caption(f"Period: {forecast.get('forecast_period', 'Next 30 days')}")
    
    # Main metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Impressions",
            f"{forecast['impressions']:,}",
            help="Expected number of times your ads will be shown"
        )
    
    with col2:
        st.metric(
            "Clicks",
            f"{forecast['clicks']:,}",
            help="Expected number of clicks on your ads"
        )
    
    with col3:
        st.metric(
            "CTR",
            f"{forecast['ctr']:.2f}%",
            help="Click-through rate (clicks ÷ impressions)"
        )
    
    with col4:
        st.metric(
            "Total Cost",
            f"${forecast['cost']:.2f}",
            help="Expected total cost for the period"
        )
    
    # Secondary metrics
    if show_details:
        st.markdown("---")
        st.subheader("💰 Cost Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Average CPC",
                f"${forecast['average_cpc']:.2f}",
                help="Average cost per click"
            )
        
        with col2:
            if forecast.get('conversions', 0) > 0:
                st.metric(
                    "Conversions",
                    f"{forecast['conversions']}",
                    help="Expected number of conversions"
                )
            else:
                st.metric("Conversions", "N/A", help="Conversion tracking not enabled")
        
        with col3:
            if forecast.get('cost_per_conversion', 0) > 0:
                st.metric(
                    "Cost/Conversion",
                    f"${forecast['cost_per_conversion']:.2f}",
                    help="Average cost per conversion"
                )
            else:
                st.metric("Cost/Conversion", "N/A", help="Conversion tracking not enabled")


def render_forecast_comparison(
    forecast_low: Dict,
    forecast_medium: Dict,
    forecast_high: Dict
):
    """
    Show forecast comparison across different budget levels
    
    Args:
        forecast_low: Forecast with low budget
        forecast_medium: Forecast with medium budget
        forecast_high: Forecast with high budget
    """
    
    st.subheader("📊 Budget Impact Analysis")
    st.write("See how different budget levels affect your campaign performance")
    
    # Create comparison table
    import pandas as pd
    
    comparison_data = {
        'Metric': ['Daily Budget', 'Impressions', 'Clicks', 'CTR', 'Avg CPC', 'Cost/Day'],
        'Low Budget': [
            f"${forecast_low['cost']:.2f}",
            f"{forecast_low['impressions']:,}",
            f"{forecast_low['clicks']:,}",
            f"{forecast_low['ctr']:.2f}%",
            f"${forecast_low['average_cpc']:.2f}",
            f"${forecast_low['cost']:.2f}"
        ],
        'Medium Budget': [
            f"${forecast_medium['cost']:.2f}",
            f"{forecast_medium['impressions']:,}",
            f"{forecast_medium['clicks']:,}",
            f"{forecast_medium['ctr']:.2f}%",
            f"${forecast_medium['average_cpc']:.2f}",
            f"${forecast_medium['cost']:.2f}"
        ],
        'High Budget': [
            f"${forecast_high['cost']:.2f}",
            f"{forecast_high['impressions']:,}",
            f"{forecast_high['clicks']:,}",
            f"{forecast_high['ctr']:.2f}%",
            f"${forecast_high['average_cpc']:.2f}",
            f"${forecast_high['cost']:.2f}"
        ]
    }
    
    df = pd.DataFrame(comparison_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Recommendation
    st.markdown("---")
    st.subheader("💡 Recommendation")
    
    # Determine best budget based on efficiency
    efficiency_low = forecast_low['clicks'] / forecast_low['cost'] if forecast_low['cost'] > 0 else 0
    efficiency_med = forecast_medium['clicks'] / forecast_medium['cost'] if forecast_medium['cost'] > 0 else 0
    efficiency_high = forecast_high['clicks'] / forecast_high['cost'] if forecast_high['cost'] > 0 else 0
    
    if efficiency_med > efficiency_low and efficiency_med > efficiency_high:
        st.success(f"✅ **Medium budget (${forecast_medium['cost']:.2f}/day)** offers the best cost efficiency!")
    elif efficiency_high > efficiency_low:
        st.success(f"✅ **Higher budget (${forecast_high['cost']:.2f}/day)** recommended for maximum reach!")
    else:
        st.info(f"💡 **Start with lower budget (${forecast_low['cost']:.2f}/day)** and scale based on performance")


def render_forecast_chart(forecast: Dict):
    """
    Render forecast as visual chart
    
    Args:
        forecast: Dictionary with forecast data
    """
    import pandas as pd
    
    # Create daily breakdown (simulate)
    days = 30
    daily_impressions = forecast['impressions'] / days
    daily_clicks = forecast['clicks'] / days
    daily_cost = forecast['cost'] / days
    
    # Create data for chart
    chart_data = pd.DataFrame({
        'Day': range(1, days + 1),
        'Impressions': [daily_impressions * (1 + i * 0.01) for i in range(days)],
        'Clicks': [daily_clicks * (1 + i * 0.01) for i in range(days)],
        'Cost': [daily_cost * (1 + i * 0.005) for i in range(days)]
    })
    
    # Show chart
    st.subheader("📈 Projected Performance Over Time")
    
    tab1, tab2, tab3 = st.tabs(["Impressions", "Clicks", "Cost"])
    
    with tab1:
        st.line_chart(chart_data, x='Day', y='Impressions')
    
    with tab2:
        st.line_chart(chart_data, x='Day', y='Clicks')
    
    with tab3:
        st.line_chart(chart_data, x='Day', y='Cost')


def render_forecast_summary_card(forecast: Dict):
    """
    Render compact forecast summary (for wizard review step)
    
    Args:
        forecast: Dictionary with forecast data
    """
    
    is_mock = forecast.get('is_mock', False)
    
    with st.container(border=True):
        st.markdown("### 🔮 Performance Forecast")
        
        if is_mock:
            st.caption("📚 Educational mock data")
        else:
            st.caption("✅ Google Ads API data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Impressions:** {forecast['impressions']:,}")
            st.write(f"**Clicks:** {forecast['clicks']:,}")
            st.write(f"**CTR:** {forecast['ctr']:.2f}%")
        
        with col2:
            st.write(f"**Avg CPC:** ${forecast['average_cpc']:.2f}")
            st.write(f"**Total Cost:** ${forecast['cost']:.2f}")
            st.write(f"**Period:** {forecast['forecast_period']}")
        
        # Expandable details
        with st.expander("📊 See Full Forecast Details"):
            render_forecast_metrics(forecast, show_details=True)
