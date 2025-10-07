# /app/dashboard_page.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def render_dashboard():
    """Renders the main dashboard with Google Ads-style interface."""
    
    df = st.session_state.get('simulation_results')

    if df is None or df.empty:
        st.warning("📋 No campaign data available. Create and run a new campaign to see results.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 **Get Started:**\n\n1. Go to Campaign Wizard\n2. Set up your campaign\n3. Run simulation\n4. View results here")
        with col2:
            st.info("📊 **What you'll see:**\n\n- Performance metrics\n- Time series charts\n- Keyword analysis\n- Budget pacing")
        return

    # ========== DATA PREPARATION ==========
    numeric_cols = ['cost', 'conversions', 'clicks', 'impressions', 'revenue', 'day', 'hour']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['day'] = df['day'].astype(int)
    df['hour'] = df['hour'].astype(int)
    
    # Create datetime for visualization
    base_date = pd.Timestamp('2024-01-01')
    df['datetime'] = base_date + pd.to_timedelta(df['day'] - 1, unit='D') + pd.to_timedelta(df['hour'], unit='h')
    
    # ========== CALCULATE METRICS ==========
    total_clicks = int(df['clicks'].sum())
    total_impressions = int(df['impressions'].sum())
    total_cost = float(df['cost'].sum())
    total_conversions = int(df['conversions'].sum())
    total_revenue = float(df['revenue'].sum())
    
    avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    roas = (total_revenue / total_cost) if total_cost > 0 else 0
    avg_position = df['position'].mean() if 'position' in df.columns else 0
    cpm = (total_cost / total_impressions * 1000) if total_impressions > 0 else 0
    
    # ========== HEADER ==========
    col1, col2, col3 = st.columns([2, 3, 1])
    with col1:
        campaign_name = df['campaign'].iloc[0] if 'campaign' in df.columns else "Campaign"
        st.subheader(f"📊 {campaign_name}")
    with col2:
        # Date range display
        start_date = df['datetime'].min().strftime('%b %d, %Y')
        end_date = df['datetime'].max().strftime('%b %d, %Y')
        st.markdown(f"<div style='text-align: center; padding: 10px; color: #666;'>📅 {start_date} - {end_date}</div>", unsafe_allow_html=True)
    with col3:
        using_real_data = df.get('using_real_data', pd.Series([False])).any()
        if using_real_data:
            st.success("✅ API Data")
        else:
            st.info("📚 Mock")

    # ========== GOOGLE ADS STYLE METRIC CARDS ==========
    # Initialize selected metrics if not exists
    if 'dashboard_metrics' not in st.session_state:
        st.session_state.dashboard_metrics = ['Clicks', 'Impressions', 'Avg. CPC', 'Cost']
    
    # Available metrics with their values and colors
    metrics_data = {
        'Clicks': {'value': total_clicks, 'format': 'number', 'color': '#4285F4'},
        'Impressions': {'value': total_impressions, 'format': 'number', 'color': '#EA4335'},
        'Avg. CPC': {'value': avg_cpc, 'format': 'currency', 'color': '#FBBC04'},
        'Cost': {'value': total_cost, 'format': 'currency', 'color': '#34A853'},
        'Conversions': {'value': total_conversions, 'format': 'number', 'color': '#34A853'},
        'Conv. rate': {'value': cvr, 'format': 'percent', 'color': '#4285F4'},
        'CTR': {'value': ctr, 'format': 'percent', 'color': '#FBBC04'},
        'ROAS': {'value': roas, 'format': 'decimal', 'color': '#34A853'},
        'CPM': {'value': cpm, 'format': 'currency', 'color': '#FBBC04'},
        'Avg. position': {'value': avg_position, 'format': 'decimal', 'color': '#4285F4'}
    }
    
    def format_metric_value(value, format_type):
        if format_type == 'number':
            if value >= 1000:
                return f"{value/1000:.1f}K"
            return f"{int(value)}"
        elif format_type == 'currency':
            return f"${value:.2f}"
        elif format_type == 'percent':
            return f"{value:.2f}%"
        elif format_type == 'decimal':
            return f"{value:.2f}"
        return str(value)
    
    # Create 4 metric card columns
    cols = st.columns(4)
    
    for idx, col in enumerate(cols):
        with col:
            current_metric = st.session_state.dashboard_metrics[idx]
            metric_info = metrics_data[current_metric]
            
            # Dropdown selector for metric
            selected = st.selectbox(
                label="Select Metric",
                options=list(metrics_data.keys()),
                index=list(metrics_data.keys()).index(current_metric),
                key=f"metric_selector_{idx}",
                label_visibility="collapsed"
            )
            
            # Update session state if changed
            if selected != current_metric:
                st.session_state.dashboard_metrics[idx] = selected
                st.rerun()
            
            # Display metric value in large text with color
            metric_info = metrics_data[selected]
            formatted_value = format_metric_value(metric_info['value'], metric_info['format'])
            
            st.markdown(f"""
            <div style='
                background: {metric_info['color']};
                color: white;
                padding: 30px 20px;
                border-radius: 4px;
                text-align: center;
                margin-top: 5px;
            '>
                <div style='font-size: 36px; font-weight: 700;'>{formatted_value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Action buttons row
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("📊 Metrics", use_container_width=True):
            st.session_state.show_metrics_panel = not st.session_state.get('show_metrics_panel', False)
    with col2:
        if st.button("⚙️ Adjust", use_container_width=True):
            st.session_state.show_adjust_panel = not st.session_state.get('show_adjust_panel', False)
    
    # Metrics Panel
    if st.session_state.get('show_metrics_panel', False):
        st.markdown("---")
        st.subheader("📊 Customize Metrics Display")
        
        available_metrics = [
            'Clicks', 'Impressions', 'Avg. CPC', 'Cost', 'Conversions', 
            'Conv. rate', 'CTR', 'Avg. position', 'Quality Score', 'Search Impression Share'
        ]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Available Metrics:**")
            for metric in available_metrics:
                if metric not in st.session_state.dashboard_metrics:
                    if st.button(f"+ {metric}", key=f"add_{metric}"):
                        st.session_state.dashboard_metrics.append(metric)
                        st.rerun()
        
        with col2:
            st.write("**Selected Metrics:**")
            metrics_to_remove = []
            for i, metric in enumerate(st.session_state.dashboard_metrics):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"• {metric}")
                with col_b:
                    if st.button("×", key=f"remove_{metric}"):
                        metrics_to_remove.append(metric)
            
            for metric in metrics_to_remove:
                st.session_state.dashboard_metrics.remove(metric)
                st.rerun()
        
        if st.button("Reset to Default", key="reset_metrics"):
            st.session_state.dashboard_metrics = ['Clicks', 'Impressions', 'Avg. CPC', 'Cost']
            st.rerun()
    
    # Adjust Settings Panel
    if st.session_state.get('show_adjust_panel', False):
        st.markdown("---")
        st.subheader("⚙️ Simulation Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Chart Settings:**")
            chart_type = st.selectbox(
                "Chart Type",
                ["Line Chart", "Bar Chart", "Area Chart"],
                key="dashboard_chart_type"
            )
            
            show_forecast = st.checkbox("Show Forecast", value=False, key="show_forecast")
            
            if show_forecast:
                forecast_days = st.slider("Forecast Days", 1, 30, 7, key="forecast_days")
        
        with col2:
            st.write("**Display Options:**")
            show_trend_lines = st.checkbox("Show Trend Lines", value=True, key="show_trends")
            show_annotations = st.checkbox("Show Data Annotations", value=False, key="show_annotations")
            auto_refresh = st.checkbox("Auto Refresh", value=False, key="auto_refresh")
            
            if auto_refresh:
                refresh_interval = st.slider("Refresh Interval (seconds)", 5, 300, 30, key="refresh_interval")
        
        st.write("**Filter Settings:**")
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            min_clicks = st.number_input("Minimum Clicks", 0, 1000, 0, key="min_clicks")
            min_impressions = st.number_input("Minimum Impressions", 0, 10000, 0, key="min_impressions")
        
        with filter_col2:
            max_cpc = st.number_input("Maximum CPC", 0.0, 100.0, 100.0, step=0.1, key="max_cpc")
            min_ctr = st.number_input("Minimum CTR (%)", 0.0, 100.0, 0.0, step=0.1, key="min_ctr")
        
        if st.button("Apply Settings", key="apply_settings"):
            st.success("✅ Settings applied! Refresh the dashboard to see changes.")
            st.rerun()

    # ========== MULTI-LINE PERFORMANCE CHART ==========
    st.subheader("Performance Over Time")
    
    # Aggregate by datetime
    time_series = df.groupby('datetime').agg({
        'clicks': 'sum',
        'impressions': 'sum',
        'cost': 'sum',
        'conversions': 'sum'
    }).reset_index().sort_values('datetime')
    
    # Create multi-line chart
    fig = go.Figure()
    
    # Add trace for each currently selected metric
    for metric_name in st.session_state.dashboard_metrics:
        metric_col_map = {
            'Clicks': 'clicks',
            'Impressions': 'impressions',
            'Cost': 'cost',
            'Conversions': 'conversions',
            'Avg. CPC': None,  # Calculated metric
            'CTR': None,
            'Conv. rate': None,
            'ROAS': None,
            'CPM': None,
            'Avg. position': None
        }
        
        col_name = metric_col_map.get(metric_name)
        if col_name and col_name in time_series.columns:
            color = metrics_data[metric_name]['color']
            fig.add_trace(go.Scatter(
                x=time_series['datetime'],
                y=time_series[col_name],
                mode='lines',
                name=metric_name,
                line=dict(color=color, width=2),
                hovertemplate=f'{metric_name}: %{{y}}<extra></extra>'
            ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=40),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(200,200,200,0.2)',
            zeroline=False
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ========== ADDITIONAL SECTIONS ==========
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔍 Keywords", "⭐ Quality Score", "💰 Budget"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Clicks", f"{total_clicks:,}")
            st.metric("Total Impressions", f"{total_impressions:,}")
            st.metric("Total Cost", f"${total_cost:,.2f}")
        
        with col2:
            st.metric("CTR", f"{ctr:.2f}%")
            st.metric("Avg. CPC", f"${avg_cpc:.2f}")
            st.metric("CPM", f"${cpm:.2f}")
        
        with col3:
            st.metric("Conversions", f"{total_conversions:,}")
            st.metric("Conv. Rate", f"{cvr:.2f}%")
            st.metric("ROAS", f"{roas:.2f}x")
    
    with tab2:
        if 'matched_keyword' in df.columns:
            keyword_agg = df.groupby('matched_keyword').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'conversions': 'sum',
                'cost': 'sum',
                'revenue': 'sum'
            }).reset_index()
            
            keyword_agg['ctr'] = (keyword_agg['clicks'] / keyword_agg['impressions'] * 100).fillna(0)
            keyword_agg['cvr'] = (keyword_agg['conversions'] / keyword_agg['clicks'] * 100).fillna(0)
            keyword_agg['cpc'] = (keyword_agg['cost'] / keyword_agg['clicks']).fillna(0)
            
            keyword_agg = keyword_agg.sort_values('cost', ascending=False).head(20)
            
            st.dataframe(
                keyword_agg,
                use_container_width=True,
                column_config={
                    "matched_keyword": "Keyword",
                    "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
                    "clicks": st.column_config.NumberColumn("Clicks", format="%d"),
                    "conversions": st.column_config.NumberColumn("Conv.", format="%d"),
                    "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
                    "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
                    "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
                    "cvr": st.column_config.NumberColumn("CVR", format="%.2f%%"),
                    "cpc": st.column_config.NumberColumn("CPC", format="$%.2f")
                },
                hide_index=True
            )
        else:
            st.info("No keyword data available")
    
    with tab3:
        if 'quality_score' in df.columns:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                avg_qs = df['quality_score'].mean()
                st.metric("Average Quality Score", f"{avg_qs:.1f}/10")
                
                if 'expected_ctr' in df.columns:
                    avg_expected_ctr = df['expected_ctr'].mean()
                    st.metric("Expected CTR", f"{(avg_expected_ctr*100):.2f}%")
                
                if 'ad_relevance' in df.columns:
                    avg_relevance = df['ad_relevance'].mean()
                    rating = "Above Avg" if avg_relevance >= 0.7 else "Average" if avg_relevance >= 0.4 else "Below Avg"
                    st.metric("Ad Relevance", rating)
            
            with col2:
                qs_counts = df['quality_score'].round().value_counts().sort_index()
                
                fig_qs = go.Figure(data=[
                    go.Bar(x=qs_counts.index, y=qs_counts.values, marker_color='#4285F4')
                ])
                
                fig_qs.update_layout(
                    title="Quality Score Distribution",
                    xaxis_title="Quality Score",
                    yaxis_title="Count",
                    height=250,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(tickmode='linear', tick0=1, dtick=1),
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig_qs, use_container_width=True)
        else:
            st.info("Quality Score data not available")
    
    with tab4:
        daily_spend = df.groupby('day').agg({'cost': 'sum'}).reset_index()
        
        campaign_config = st.session_state.get('campaign_config', {})
        daily_budget = campaign_config.get('daily_budget', 100.0)
        
        fig_budget = go.Figure()
        
        fig_budget.add_trace(go.Bar(
            x=daily_spend['day'],
            y=daily_spend['cost'],
            name='Daily Spend',
            marker_color='#EA4335'
        ))
        
        fig_budget.add_trace(go.Scatter(
            x=daily_spend['day'],
            y=[daily_budget] * len(daily_spend),
            name='Daily Budget',
            line=dict(color='#34A853', width=2, dash='dash')
        ))
        
        fig_budget.update_layout(
            xaxis_title="Day",
            yaxis_title="Spend ($)",
            height=300,
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=20, b=40)
        )
        
        st.plotly_chart(fig_budget, use_container_width=True)
        
        total_budget = daily_budget * df['day'].nunique()
        utilization = (total_cost / total_budget * 100) if total_budget > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"${total_budget:,.2f}")
        with col2:
            st.metric("Total Spend", f"${total_cost:,.2f}")
        with col3:
            st.metric("Utilization", f"{utilization:.1f}%")

    # ========== EXPORT ==========
    st.markdown("---")
    col1, col2 = st.columns([1, 5])
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export CSV",
            data=csv,
            file_name=f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
