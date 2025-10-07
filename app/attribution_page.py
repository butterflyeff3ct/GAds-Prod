# /app/attribution_page.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from features.attribution import AttributionEngine, AttributionModel, ConversionPath, TouchPoint, ConversionEvent, create_sample_conversion_path
from datetime import datetime, timedelta

def render_attribution_analysis():
    """
    Attribution Analysis Page
    Compare different attribution models and understand conversion paths.
    """
    st.header("📊 Attribution Analysis")
    
    st.info("""
    **What is Attribution?**
    
    Attribution determines how credit for conversions is distributed across touchpoints.
    Different models can show very different results from the same data!
    """)
    
    df = st.session_state.get('simulation_results')
    
    # ========== MODEL SELECTOR ==========
    st.subheader("Select Attribution Model")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_model = st.selectbox(
            "Attribution Model",
            options=[model.value for model in AttributionModel],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="attribution_model_selector"
        )
        
        attribution_engine = AttributionEngine(
            model=AttributionModel(selected_model)
        )
    
    with col2:
        if st.button("ℹ️ Explain This Model", use_container_width=True):
            st.session_state['show_model_explanation'] = True
    
    # Show model explanation if requested
    if st.session_state.get('show_model_explanation', False):
        with st.expander("📚 Model Explanation", expanded=True):
            explanation = attribution_engine.get_model_explanation()
            st.markdown(explanation)
    
    st.markdown("---")
    
    # ========== SAMPLE CONVERSION PATH ==========
    st.subheader("🎓 Educational Example: Conversion Path")
    
    st.write("""
    Let's see how different models attribute a $100 conversion across a multi-touch journey:
    """)
    
    # Create sample path
    sample_path = create_sample_conversion_path()
    
    # Display the path visually
    col1, col2, col3, col4 = st.columns(4)
    
    touchpoint_labels = ["1st Touch", "2nd Touch", "3rd Touch", "Conversion"]
    
    for i, (col, tp, label) in enumerate(zip([col1, col2, col3, col4], 
                                             sample_path.touchpoints + [sample_path.touchpoints[-1]], 
                                             touchpoint_labels)):
        with col:
            if i < len(sample_path.touchpoints):
                st.markdown(f"**{label}**")
                st.write(f"🔍 {tp.channel.title()}")
                st.caption(f"{tp.timestamp.strftime('%b %d, %I%M%p')}")
                st.caption(f"${tp.cost:.2f}")
            else:
                st.markdown(f"**{label}**")
                st.write(f"✅ Purchase")
                st.caption(f"${sample_path.conversion.value:.2f}")
    
    # Compare all models on this path
    st.subheader("💰 Credit Distribution by Model")
    
    all_models_comparison = attribution_engine.compare_attribution_models([sample_path])
    
    # Create visualization
    comparison_data = []
    for model_name, attribution in all_models_comparison.items():
        row = {'Model': model_name.replace('_', ' ').title()}
        for key, value in attribution.items():
            touchpoint_num = key.split('_')[-1]
            row[f'Touch {touchpoint_num}'] = f"${value:.2f}"
        comparison_data.append(row)
    
    st.table(comparison_data)
    
    # Visual comparison
    fig = go.Figure()
    
    for model_name, attribution in all_models_comparison.items():
        values = list(attribution.values())
        labels = [f"Touch {i+1}" for i in range(len(values))]
        
        fig.add_trace(go.Bar(
            name=model_name.replace('_', ' ').title(),
            x=labels,
            y=values
        ))
    
    fig.update_layout(
        title='Attribution Comparison: How Different Models Credit the Same Conversion',
        xaxis_title='Touchpoint',
        yaxis_title='Credit ($)',
        barmode='group',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ========== REAL CAMPAIGN DATA ANALYSIS ==========
    if df is not None and not df.empty:
        st.subheader("📈 Your Campaign Attribution")
        
        st.info("""
        For your simulated campaign, we'll analyze conversion paths and show
        how different attribution models would credit your keywords.
        """)
        
        # Create simplified conversion paths from simulation data
        # Group by user journey (simplified - in reality, track actual user IDs)
        
        if 'conversions' in df.columns and df['conversions'].sum() > 0:
            # Find converting sessions
            converting = df[df['conversions'] > 0].copy()
            
            total_conversion_value = converting['revenue'].sum()
            
            st.write(f"**Total Conversions:** {int(converting['conversions'].sum())}")
            st.write(f"**Total Conversion Value:** ${total_conversion_value:,.2f}")
            
            # Model comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Last Click Model", f"${total_conversion_value:,.2f}")
                st.caption("100% credit to last touchpoint")
            
            with col2:
                # Show how much the last keyword got
                if 'matched_keyword' in converting.columns:
                    top_keyword = converting.groupby('matched_keyword')['revenue'].sum().nlargest(1)
                    if not top_keyword.empty:
                        st.metric("Top Keyword (Last Click)", f"${top_keyword.iloc[0]:,.2f}")
                        st.caption(f"{top_keyword.index[0]}")
        else:
            st.warning("No conversions in simulation data yet. Attribution analysis requires conversion data.")
    
    else:
        st.info("Run a campaign simulation first to see attribution analysis on your data.")
    
    # ========== EDUCATIONAL RESOURCES ==========
    with st.expander("📚 Learn More About Attribution", expanded=False):
        st.markdown("""
        ### Why Attribution Matters
        
        **The Problem:**
        A customer might see your ad 5 times before converting. Which touchpoint gets credit?
        
        **The Impact:**
        - Different models show different "best performing" keywords
        - Budget allocation changes dramatically
        - ROI calculations vary by 50%+ between models
        
        ### Choosing the Right Model
        
        | Model | Best For | Pros | Cons |
        |-------|----------|------|------|
        | **Last Click** | Direct response, short sales cycles | Simple, clear | Ignores awareness |
        | **First Click** | Brand awareness campaigns | Values discovery | Ignores nurturing |
        | **Linear** | Understanding full journey | Fair | Doesn't reflect importance |
        | **Time Decay** | Retail, e-commerce | Rewards recency | Undervalues awareness |
        | **Position-Based** | Balanced view | Values first & last | Complex to explain |
        | **Data-Driven** | Large datasets | Most accurate | Needs lots of data |
        
        ### Industry Recommendations
        
        - **E-commerce:** Time Decay or Data-Driven
        - **Lead Gen:** Position-Based
        - **Brand Awareness:** First Click
        - **Direct Response:** Last Click
        - **Multi-Channel:** Data-Driven or Linear
        """)
