# /app/auction_insights_page.py
"""
Auction Insights Report
Shows competitive metrics and how you compare to other advertisers.
Key report in Google Ads for understanding competitive landscape.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.competitor_learning import CompetitorLearningEngine

def render_auction_insights():
    """
    Render Auction Insights report.
    
    Key metrics:
    - Impression Share
    - Overlap Rate (how often you and competitor appear together)
    - Position Above Rate (how often you rank higher)
    - Top of Page Rate
    - Absolute Top of Page Rate
    - Outranking Share
    """
    
    st.header("🔍 Auction Insights")
    
    st.info("""
    **What is Auction Insights?**
    
    See how your performance compares to other advertisers competing for the same auctions.
    This report shows competitive metrics you can't see anywhere else.
    """)
    
    df = st.session_state.get('simulation_results')
    
    if df is None or df.empty:
        st.warning("No data available. Run a simulation first.")
        
        # Show example/explanation
        st.subheader("📊 Sample Auction Insights Report")
        
        sample_data = {
            'Advertiser': ['You', 'Competitor A', 'Competitor B', 'Competitor C', 'Competitor D'],
            'Impression Share': ['45%', '32%', '28%', '18%', '12%'],
            'Overlap Rate': ['-', '78%', '65%', '45%', '32%'],
            'Position Above Rate': ['-', '58%', '62%', '71%', '79%'],
            'Top of Page Rate': ['72%', '68%', '52%', '41%', '35%'],
            'Absolute Top Rate': ['38%', '28%', '19%', '12%', '8%'],
            'Outranking Share': ['-', '64%', '68%', '75%', '81%']
        }
        
        st.table(sample_data)
        
        st.markdown("""
        ### Metric Definitions
        
        **Impression Share:** % of total available impressions you received
        **Overlap Rate:** How often competitor appeared when you did
        **Position Above Rate:** How often you ranked higher than competitor
        **Top of Page Rate:** % of impressions in positions 1-4
        **Absolute Top Rate:** % of impressions in position 1
        **Outranking Share:** How often you ranked higher OR showed when they didn't
        """)
        
        return
    
    # ========== CALCULATE AUCTION INSIGHTS METRICS ==========
    st.subheader("Your Auction Insights Report")
    
    # Your metrics
    your_impressions = df['impressions'].sum()
    your_cost = df['cost'].sum()
    your_clicks = df['clicks'].sum()
    
    # Position data
    if 'position' in df.columns:
        top_of_page_count = len(df[df['position'] <= 4])
        absolute_top_count = len(df[df['position'] == 1])
        total_count = len(df)
        
        top_of_page_rate = (top_of_page_count / total_count * 100) if total_count > 0 else 0
        absolute_top_rate = (absolute_top_count / total_count * 100) if total_count > 0 else 0
        avg_position = df['position'].mean()
    else:
        top_of_page_rate = 70
        absolute_top_rate = 35
        avg_position = 2.5
    
    # Estimate total market impressions (you don't see all auctions)
    # Competitor analysis from simulation
    competitor_engine = CompetitorLearningEngine(num_competitors=8)
    competitor_insights = competitor_engine.get_competitor_insights()
    
    # Calculate estimated impression share
    # Assume total market is 2-3x your impressions
    estimated_market_impressions = your_impressions * 2.5
    your_impression_share = (your_impressions / estimated_market_impressions * 100)
    
    # ========== SUMMARY METRICS ==========
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Your Impression Share", f"{your_impression_share:.1f}%")
    
    with col2:
        st.metric("Avg. Position", f"{avg_position:.1f}")
    
    with col3:
        st.metric("Top of Page Rate", f"{top_of_page_rate:.1f}%")
    
    with col4:
        st.metric("Absolute Top Rate", f"{absolute_top_rate:.1f}%")
    
    st.markdown("---")
    
    # ========== COMPETITIVE COMPARISON TABLE ==========
    st.subheader("📊 Competitive Landscape")
    
    # Generate realistic competitor data
    competitors_data = []
    
    # Your data (first row)
    competitors_data.append({
        'Advertiser': 'You',
        'Impression Share (%)': round(your_impression_share, 1),
        'Avg Position': round(avg_position, 1),
        'Overlap Rate (%)': '-',
        'Position Above Rate (%)': '-',
        'Top of Page Rate (%)': round(top_of_page_rate, 1),
        'Absolute Top Rate (%)': round(absolute_top_rate, 1),
        'Outranking Share (%)': '-'
    })
    
    # Generate competitor data (educational simulation)
    competitor_names = ['Competitor A', 'Competitor B', 'Competitor C', 'Competitor D', 'Competitor E']
    
    # Distribute remaining impression share among competitors
    remaining_is = 100 - your_impression_share
    
    for i, comp_name in enumerate(competitor_names):
        # Decreasing impression shares
        comp_is = remaining_is * (0.35 - i * 0.05)
        
        # Overlap rate (how often they appear with you)
        # Higher IS = higher overlap
        overlap_rate = min(95, 60 + (comp_is * 0.8))
        
        # Position above rate (how often you beat them)
        # Your position vs their estimated position
        comp_avg_position = 2.0 + (i * 0.5)
        position_above = 100 if avg_position < comp_avg_position else max(20, 100 - (comp_avg_position - avg_position) * 30)
        
        # Top of page rate
        comp_top_rate = max(20, top_of_page_rate - (i * 8))
        
        # Absolute top rate
        comp_abs_top = max(5, absolute_top_rate - (i * 5))
        
        # Outranking share
        outranking = position_above * 0.85 + (1 - overlap_rate/100) * 15
        
        competitors_data.append({
            'Advertiser': comp_name,
            'Impression Share (%)': round(comp_is, 1),
            'Avg Position': round(comp_avg_position, 1),
            'Overlap Rate (%)': round(overlap_rate, 1),
            'Position Above Rate (%)': round(position_above, 1),
            'Top of Page Rate (%)': round(comp_top_rate, 1),
            'Absolute Top Rate (%)': round(comp_abs_top, 1),
            'Outranking Share (%)': round(outranking, 1)
        })
    
    # Display table
    insights_df = pd.DataFrame(competitors_data)
    
    st.dataframe(
        insights_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Advertiser": st.column_config.TextColumn("Advertiser", width="medium"),
            "Impression Share (%)": st.column_config.NumberColumn("Impr. Share", format="%.1f%%"),
            "Avg Position": st.column_config.NumberColumn("Avg Pos", format="%.1f"),
            "Overlap Rate (%)": "Overlap Rate",
            "Position Above Rate (%)": "Position Above",
            "Top of Page Rate (%)": "Top of Page",
            "Absolute Top Rate (%)": "Abs. Top",
            "Outranking Share (%)": "Outranking"
        }
    )
    
    # ========== VISUALIZATIONS ==========
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Impression Share comparison
        fig_is = go.Figure(data=[
            go.Bar(
                x=[row['Advertiser'] for row in competitors_data],
                y=[row['Impression Share (%)'] for row in competitors_data],
                marker_color=['#4285F4' if row['Advertiser'] == 'You' else '#E8EAED' for row in competitors_data],
                text=[f"{row['Impression Share (%)']}%" for row in competitors_data],
                textposition='outside'
            )
        ])
        
        fig_is.update_layout(
            title='Impression Share Comparison',
            xaxis_title='',
            yaxis_title='Impression Share (%)',
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig_is, use_container_width=True)
    
    with col2:
        # Position comparison
        fig_pos = go.Figure(data=[
            go.Bar(
                x=[row['Advertiser'] for row in competitors_data[:6]],
                y=[row['Avg Position'] for row in competitors_data[:6]],
                marker_color=['#34A853' if row['Advertiser'] == 'You' else '#E8EAED' for row in competitors_data[:6]],
                text=[f"{row['Avg Position']}" for row in competitors_data[:6]],
                textposition='outside'
            )
        ])
        
        fig_pos.update_layout(
            title='Average Position Comparison',
            xaxis_title='',
            yaxis_title='Average Position',
            height=350,
            showlegend=False,
            yaxis=dict(autorange='reversed')  # Lower position number = better
        )
        
        st.plotly_chart(fig_pos, use_container_width=True)
    
    # ========== INSIGHTS & RECOMMENDATIONS ==========
    st.markdown("---")
    st.subheader("💡 Competitive Insights & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎯 Your Competitive Position:**")
        
        if your_impression_share > 40:
            st.success("✅ **Strong Market Position**")
            st.write("You're capturing a significant share of available impressions.")
        elif your_impression_share > 25:
            st.info("📊 **Moderate Market Position**")
            st.write("You have a decent presence but room to grow.")
        else:
            st.warning("⚠️ **Low Market Position**")
            st.write("You're missing most available impressions.")
        
        # Specific recommendations
        st.write("\n**Recommendations:**")
        
        if your_impression_share < 50:
            lost_is = 100 - your_impression_share - sum(row['Impression Share (%)'] for row in competitors_data[1:])
            st.write(f"• ~{lost_is:.0f}% of impressions are still uncaptured")
            st.write("• Opportunity to increase budget and gain more traffic")
        
        if avg_position > 3:
            st.write("• Average position is low - consider increasing bids")
            st.write("• Improve Quality Score to rank higher at same cost")
        
        if absolute_top_rate < 30:
            st.write("• Rarely appearing in position 1")
            st.write("• Use Target Impression Share (Absolute Top) if position 1 is critical")
    
    with col2:
        st.write("**🏆 Competitive Advantages:**")
        
        # Calculate competitive strengths
        top_comp_is = competitors_data[1]['Impression Share (%)'] if len(competitors_data) > 1 else 0
        
        if your_impression_share > top_comp_is:
            st.success(f"✅ You lead in impression share (+{your_impression_share - top_comp_is:.1f}%)")
        
        if avg_position < 2.5:
            st.success("✅ Your average position is strong")
        
        if top_of_page_rate > 70:
            st.success("✅ High top-of-page rate (70%+)")
        
        if absolute_top_rate > 35:
            st.success("✅ Strong absolute top performance")
        
        # Weaknesses
        st.write("\n**⚠️ Areas to Improve:**")
        
        if your_impression_share < top_comp_is:
            st.write(f"• Competitor A has higher IS ({top_comp_is:.1f}% vs your {your_impression_share:.1f}%)")
        
        if top_of_page_rate < 50:
            st.write(f"• Top of page rate is low ({top_of_page_rate:.1f}%)")
        
        if absolute_top_rate < 20:
            st.write(f"• Rarely in position 1 ({absolute_top_rate:.1f}%)")
    
    # ========== TREND ANALYSIS ==========
    if 'day' in df.columns and df['day'].nunique() > 3:
        st.markdown("---")
        st.subheader("📈 Impression Share Trends")
        
        # Daily impression share (simplified calculation)
        daily_is = df.groupby('day').agg({
            'impressions': 'sum'
        }).reset_index()
        
        # Estimate daily IS (your impressions / estimated market)
        daily_is['impression_share'] = (daily_is['impressions'] / (daily_is['impressions'] * 2.5) * 100)
        
        fig_trend = go.Figure()
        
        fig_trend.add_trace(go.Scatter(
            x=daily_is['day'],
            y=daily_is['impression_share'],
            mode='lines+markers',
            name='Your Impression Share',
            line=dict(color='#4285F4', width=3),
            marker=dict(size=8)
        ))
        
        # Add target line if using Target IS bidding
        campaign_config = st.session_state.get('campaign_config', {})
        target_is = campaign_config.get('target_impression_share')
        
        if target_is:
            fig_trend.add_trace(go.Scatter(
                x=daily_is['day'],
                y=[target_is] * len(daily_is),
                mode='lines',
                name='Target IS',
                line=dict(color='#34A853', width=2, dash='dash')
            ))
        
        fig_trend.update_layout(
            xaxis_title='Day',
            yaxis_title='Impression Share (%)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    
    # ========== EDUCATIONAL GUIDE ==========
    with st.expander("📚 How to Use Auction Insights", expanded=False):
        st.markdown("""
        ### Understanding the Metrics
        
        **Impression Share:**
        - Your share of total available impressions
        - Higher = more visibility
        - Typical range: 20-60%
        
        **Overlap Rate:**
        - How often you and competitor appear together
        - High overlap = direct competition
        - Use to identify main competitors
        
        **Position Above Rate:**
        - When appearing together, how often you rank higher
        - >50% = you're winning
        - <50% = they're winning
        
        **Outranking Share:**
        - Combines position above + times you showed when they didn't
        - Best overall competitive metric
        - >70% = strong competitive position
        
        ### Strategic Actions
        
        **If a competitor has higher IS than you:**
        1. Check their Position Above Rate
        2. If they rank higher: Improve QS or increase bids
        3. If you rank higher: Increase budget to show more often
        
        **If overlap rate is high (>70%):**
        - You're in direct competition
        - Consider: Differentiation, niche targeting, or outbid them
        
        **If position above rate is low (<40%):**
        - They're beating you in the auction
        - Action: Improve Quality Score, increase bids, or both
        
        ### Example Analysis
        
        ```
        Competitor A:
        - IS: 32% (you have 45% ✅)
        - Overlap: 78% (high - direct competitor)
        - Position Above: 58% (you win more often ✅)
        - Outranking: 64% (you dominate ✅)
        
        Verdict: You're winning against Competitor A
        Action: Maintain current strategy
        ```
        
        ```
        Competitor B:
        - IS: 28% (you have 45% ✅)
        - Overlap: 65% (moderate competition)
        - Position Above: 42% (they win slightly more ⚠️)
        - Outranking: 52% (close race)
        
        Verdict: Competitive, they rank higher
        Action: Improve Quality Score or increase bids
        ```
        """)
    
    # Export
    st.markdown("---")
    
    csv = insights_df.to_csv(index=False)
    st.download_button(
        label="📥 Export Auction Insights",
        data=csv,
        file_name="auction_insights.csv",
        mime="text/csv"
    )
