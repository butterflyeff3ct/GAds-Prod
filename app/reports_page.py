# /app/reports_page.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def render_reports():
    """Renders detailed, sliceable reports with advanced analytics."""
    st.header("📊 Campaign Reports")
    
    df = st.session_state.get('simulation_results')
    if df is None or df.empty:
        st.warning("No data available. Run a simulation first.")
        return

    # Ensure numeric columns
    numeric_cols = ['impressions', 'clicks', 'conversions', 'cost', 'revenue', 'position', 'day', 'hour']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # ========== REPORT TYPE SELECTOR ==========
    st.subheader("Select Report Type")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        report_type = st.selectbox(
            "Report",
            ["Overview", "Keyword Performance", "Device Performance", "Geographic", 
             "Hour of Day", "Day of Week", "Position Analysis", "Search Terms", "Quality Score"],
            key="report_type_selector"
        )
    
    with col2:
        # Date range filter (if simulation has multiple days)
        if 'day' in df.columns and df['day'].nunique() > 1:
            day_range = st.slider(
                "Day Range",
                min_value=int(df['day'].min()),
                max_value=int(df['day'].max()),
                value=(int(df['day'].min()), int(df['day'].max())),
                key="day_range_filter"
            )
            df = df[(df['day'] >= day_range[0]) & (df['day'] <= day_range[1])]

    st.markdown("---")

    # ========== OVERVIEW REPORT ==========
    if report_type == "Overview":
        st.subheader("Campaign Overview")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_impressions = df['impressions'].sum()
        total_clicks = df['clicks'].sum()
        total_cost = df['cost'].sum()
        total_conversions = df['conversions'].sum()
        
        with col1:
            st.metric("Impressions", f"{int(total_impressions):,}")
            st.metric("CTR", f"{(total_clicks/total_impressions*100):.2f}%" if total_impressions > 0 else "0%")
        with col2:
            st.metric("Clicks", f"{int(total_clicks):,}")
            st.metric("CPC", f"${(total_cost/total_clicks):.2f}" if total_clicks > 0 else "$0.00")
        with col3:
            st.metric("Cost", f"${total_cost:,.2f}")
            st.metric("Conversions", f"{int(total_conversions):,}")
        with col4:
            cvr = (total_conversions/total_clicks*100) if total_clicks > 0 else 0
            st.metric("CVR", f"{cvr:.2f}%")
            cpa = (total_cost/total_conversions) if total_conversions > 0 else 0
            st.metric("CPA", f"${cpa:.2f}")
        
        # Performance trends
        st.subheader("Performance Trends")
        
        if 'day' in df.columns and 'hour' in df.columns:
            # Create datetime
            base_date = pd.Timestamp('2024-01-01')
            df['datetime'] = base_date + pd.to_timedelta(df['day'] - 1, unit='D') + pd.to_timedelta(df['hour'], unit='h')
            
            daily_metrics = df.groupby('day').agg({
                'impressions': 'sum',
                'clicks': 'sum',
                'cost': 'sum',
                'conversions': 'sum'
            }).reset_index()
            
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Daily Clicks', 'Daily Cost', 'Daily CTR', 'Daily CVR')
            )
            
            # Clicks
            fig.add_trace(go.Scatter(x=daily_metrics['day'], y=daily_metrics['clicks'], 
                                    mode='lines+markers', name='Clicks'), row=1, col=1)
            
            # Cost
            fig.add_trace(go.Scatter(x=daily_metrics['day'], y=daily_metrics['cost'], 
                                    mode='lines+markers', name='Cost', line=dict(color='red')), row=1, col=2)
            
            # CTR
            daily_metrics['ctr'] = (daily_metrics['clicks'] / daily_metrics['impressions'] * 100).fillna(0)
            fig.add_trace(go.Scatter(x=daily_metrics['day'], y=daily_metrics['ctr'], 
                                    mode='lines+markers', name='CTR', line=dict(color='orange')), row=2, col=1)
            
            # CVR
            daily_metrics['cvr'] = (daily_metrics['conversions'] / daily_metrics['clicks'] * 100).fillna(0)
            fig.add_trace(go.Scatter(x=daily_metrics['day'], y=daily_metrics['cvr'], 
                                    mode='lines+markers', name='CVR', line=dict(color='green')), row=2, col=2)
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # ========== KEYWORD REPORT ==========
    elif report_type == "Keyword Performance":
        st.subheader("Keyword Performance Analysis")
        
        if 'matched_keyword' not in df.columns:
            st.error("Keyword data not available")
            return
        
        # Aggregate by keyword
        keyword_agg = df.groupby('matched_keyword').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'cost': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        # Calculate metrics
        keyword_agg['ctr'] = (keyword_agg['clicks'] / keyword_agg['impressions'] * 100).fillna(0)
        keyword_agg['cvr'] = (keyword_agg['conversions'] / keyword_agg['clicks'] * 100).fillna(0)
        keyword_agg['cpc'] = (keyword_agg['cost'] / keyword_agg['clicks']).fillna(0)
        keyword_agg['cpa'] = (keyword_agg['cost'] / keyword_agg['conversions']).fillna(0)
        keyword_agg['roas'] = (keyword_agg['revenue'] / keyword_agg['cost']).fillna(0)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox("Sort by", 
                                  ['cost', 'clicks', 'conversions', 'ctr', 'cvr', 'roas'],
                                  key="kw_sort")
        with col2:
            min_clicks = st.number_input("Min Clicks", min_value=0, value=0, key="kw_min_clicks")
        with col3:
            top_n = st.number_input("Show Top N", min_value=5, max_value=100, value=20, key="kw_top_n")
        
        # Apply filters and sort
        filtered = keyword_agg[keyword_agg['clicks'] >= min_clicks]
        filtered = filtered.sort_values(sort_by, ascending=False).head(top_n)
        
        # Display table
        st.dataframe(
            filtered,
            use_container_width=True,
            column_config={
                "matched_keyword": "Keyword",
                "impressions": st.column_config.NumberColumn("Impr.", format="%d"),
                "clicks": st.column_config.NumberColumn("Clicks", format="%d"),
                "conversions": st.column_config.NumberColumn("Conv.", format="%d"),
                "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
                "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
                "cvr": st.column_config.NumberColumn("CVR", format="%.2f%%"),
                "cpc": st.column_config.NumberColumn("CPC", format="$%.2f"),
                "cpa": st.column_config.NumberColumn("CPA", format="$%.2f"),
                "roas": st.column_config.NumberColumn("ROAS", format="%.2fx")
            },
            hide_index=True
        )
        
        # Visualization
        fig = px.scatter(filtered, x='cpc', y='conversions', size='cost', 
                        color='roas', hover_name='matched_keyword',
                        labels={'cpc': 'CPC ($)', 'conversions': 'Conversions', 'cost': 'Spend', 'roas': 'ROAS'},
                        title='Keyword Performance: CPC vs Conversions')
        st.plotly_chart(fig, use_container_width=True)

    # ========== DEVICE REPORT ==========
    elif report_type == "Device Performance":
        st.subheader("Device Performance Comparison")
        
        if 'device' not in df.columns:
            st.error("Device data not available")
            return
        
        device_agg = df.groupby('device').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'cost': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        device_agg['ctr'] = (device_agg['clicks'] / device_agg['impressions'] * 100).fillna(0)
        device_agg['cvr'] = (device_agg['conversions'] / device_agg['clicks'] * 100).fillna(0)
        device_agg['cpc'] = (device_agg['cost'] / device_agg['clicks']).fillna(0)
        device_agg['roas'] = (device_agg['revenue'] / device_agg['cost']).fillna(0)
        
        st.dataframe(device_agg, use_container_width=True, hide_index=True)
        
        # Visualization
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('Clicks by Device', 'Cost by Device', 'Conversions by Device'),
            specs=[[{'type':'pie'}, {'type':'pie'}, {'type':'pie'}]]
        )
        
        fig.add_trace(go.Pie(labels=device_agg['device'], values=device_agg['clicks'], name='Clicks'), 1, 1)
        fig.add_trace(go.Pie(labels=device_agg['device'], values=device_agg['cost'], name='Cost'), 1, 2)
        fig.add_trace(go.Pie(labels=device_agg['device'], values=device_agg['conversions'], name='Conv'), 1, 3)
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # ========== HOURLY REPORT ==========
    elif report_type == "Hour of Day":
        st.subheader("Hour of Day Performance")
        
        if 'hour' not in df.columns:
            st.error("Hour data not available")
            return
        
        hourly_agg = df.groupby('hour').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'cost': 'sum'
        }).reset_index()
        
        hourly_agg['ctr'] = (hourly_agg['clicks'] / hourly_agg['impressions'] * 100).fillna(0)
        hourly_agg['cvr'] = (hourly_agg['conversions'] / hourly_agg['clicks'] * 100).fillna(0)
        hourly_agg['cpc'] = (hourly_agg['cost'] / hourly_agg['clicks']).fillna(0)
        
        # Heatmap style visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Clicks by Hour', 'Cost by Hour', 'CTR by Hour', 'CVR by Hour')
        )
        
        fig.add_trace(go.Bar(x=hourly_agg['hour'], y=hourly_agg['clicks']), 1, 1)
        fig.add_trace(go.Bar(x=hourly_agg['hour'], y=hourly_agg['cost']), 1, 2)
        fig.add_trace(go.Scatter(x=hourly_agg['hour'], y=hourly_agg['ctr'], mode='lines+markers'), 2, 1)
        fig.add_trace(go.Scatter(x=hourly_agg['hour'], y=hourly_agg['cvr'], mode='lines+markers'), 2, 2)
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Best/worst hours
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🌟 Best Performing Hours")
            best_hours = hourly_agg.nlargest(5, 'conversions')[['hour', 'clicks', 'conversions', 'cost']]
            st.dataframe(best_hours, hide_index=True)
        with col2:
            st.subheader("📉 Lowest Performing Hours")
            worst_hours = hourly_agg.nsmallest(5, 'conversions')[['hour', 'clicks', 'conversions', 'cost']]
            st.dataframe(worst_hours, hide_index=True)

    # ========== POSITION ANALYSIS ==========
    elif report_type == "Position Analysis":
        st.subheader("Ad Position Performance")
        
        if 'position' not in df.columns:
            st.error("Position data not available")
            return
        
        position_agg = df.groupby('position').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'cost': 'sum'
        }).reset_index()
        
        position_agg['ctr'] = (position_agg['clicks'] / position_agg['impressions'] * 100).fillna(0)
        position_agg['cvr'] = (position_agg['conversions'] / position_agg['clicks'] * 100).fillna(0)
        
        st.dataframe(position_agg, use_container_width=True, hide_index=True)
        
        # Position impact visualization
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=position_agg['position'], y=position_agg['ctr'], 
                                mode='lines+markers', name='CTR', yaxis='y'))
        fig.add_trace(go.Scatter(x=position_agg['position'], y=position_agg['cvr'], 
                                mode='lines+markers', name='CVR', yaxis='y2'))
        
        fig.update_layout(
            title='CTR and CVR by Ad Position',
            xaxis=dict(title='Position'),
            yaxis=dict(title='CTR (%)', side='left'),
            yaxis2=dict(title='CVR (%)', side='right', overlaying='y'),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # ========== QUALITY SCORE REPORT ==========
    elif report_type == "Quality Score":
        st.subheader("Quality Score Analysis")
        
        if 'quality_score' not in df.columns:
            st.error("Quality Score data not available")
            return
        
        avg_qs = df['quality_score'].mean()
        median_qs = df['quality_score'].median()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average QS", f"{avg_qs:.1f}/10")
        with col2:
            st.metric("Median QS", f"{median_qs:.1f}/10")
        with col3:
            high_qs_pct = (df['quality_score'] >= 7).sum() / len(df) * 100
            st.metric("High QS (7+)", f"{high_qs_pct:.1f}%")
        
        # Distribution
        qs_dist = df['quality_score'].round().value_counts().sort_index()
        fig = go.Figure(data=[go.Bar(x=qs_dist.index, y=qs_dist.values)])
        fig.update_layout(title='Quality Score Distribution', xaxis_title='Quality Score', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)
        
        # QS component analysis
        if all(col in df.columns for col in ['expected_ctr', 'ad_relevance', 'landing_page_exp']):
            st.subheader("Quality Score Components")
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_ctr = df['expected_ctr'].mean()
                st.metric("Avg Expected CTR", f"{(avg_ctr*100):.2f}%")
            with col2:
                avg_rel = df['ad_relevance'].mean()
                rating = "Above Avg" if avg_rel >= 0.7 else "Average" if avg_rel >= 0.4 else "Below Avg"
                st.metric("Ad Relevance", rating)
            with col3:
                avg_lp = df['landing_page_exp'].mean()
                rating = "Above Avg" if avg_lp >= 0.7 else "Average" if avg_lp >= 0.4 else "Below Avg"
                st.metric("Landing Page", rating)

    st.markdown("---")
    
    # Export button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Export Current Report",
        data=csv,
        file_name=f"{report_type.lower().replace(' ', '_')}_report.csv",
        mime="text/csv"
    )
