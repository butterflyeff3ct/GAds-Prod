# /app/planner_page.py
import streamlit as st
import pandas as pd
from features.planner import fetch_keyword_data, KWPSource, GOOGLE_ADS_API_AVAILABLE

def render_keyword_planner():
    """Renders the keyword planner interface."""
    st.header("🔍 Keyword Planner")
    
    st.write("""
    Research keywords and get search volume data, competition levels, and CPC estimates.
    This helps you discover new keywords for your campaigns.
    """)
    
    # Data source indicator (read-only, controlled by sidebar)
    use_api = st.session_state.get('use_api_data', True) and GOOGLE_ADS_API_AVAILABLE
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Keyword Research")
    with col2:
        if use_api:
            st.success("✅ Google Ads API")
        else:
            st.info("📚 Mock Data")
    
    if not GOOGLE_ADS_API_AVAILABLE:
        st.info("💡 Google Ads API not configured. Using educational mock data. Toggle in sidebar settings.")
    
    # Keyword input
    st.subheader("Enter Keywords or Phrases")
    keyword_input = st.text_area(
        "Enter keywords (one per line)",
        placeholder="iphone 17\napple phone\nsmartphone deals\nbest phone 2024",
        height=150,
        help="Enter seed keywords to research. One keyword per line."
    )
    
    # Location targeting (optional)
    with st.expander("🌍 Location Targeting (Optional)"):
        location_input = st.text_input(
            "Target locations",
            placeholder="United States, United Kingdom, Canada",
            help="Enter countries or regions separated by commas"
        )
    
    # Search button
    if st.button("🔍 Get Keyword Ideas", type="primary"):
        if not keyword_input.strip():
            st.error("Please enter at least one keyword")
            return
        
        # Parse keywords
        seed_keywords = [kw.strip() for kw in keyword_input.split('\n') if kw.strip()]
        
        with st.spinner(f"Fetching keyword data for {len(seed_keywords)} keywords..."):
            # Determine source from session state
            source = KWPSource.GOOGLE_ADS_API if use_api else KWPSource.MOCK
            
            # Parse locations (if provided)
            location_ids = None
            if location_input:
                location_ids = [loc.strip() for loc in location_input.split(',') if loc.strip()]
            
            # Fetch data
            try:
                df = fetch_keyword_data(
                    seed_keywords=seed_keywords,
                    source=source,
                    location_ids=location_ids
                )
                
                if df.empty:
                    st.warning("No keyword data returned. Try different keywords.")
                    return
                
                st.success(f"✅ Found {len(df)} keyword ideas!")
                
                # Display results
                st.subheader("📊 Keyword Ideas")
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Keywords", len(df))
                with col2:
                    avg_searches = df['avg_monthly_searches'].mean()
                    st.metric("Avg Monthly Searches", f"{int(avg_searches):,}")
                with col3:
                    avg_cpc = df['cpc_low'].mean()
                    st.metric("Avg CPC (Low)", f"${avg_cpc:.2f}")
                
                # Filters
                st.subheader("🔧 Filter Results")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_searches = st.number_input(
                        "Min Monthly Searches",
                        min_value=0,
                        value=0,
                        step=100,
                        key="planner_min_searches"
                    )
                
                with col2:
                    competition_filter = st.multiselect(
                        "Competition Level",
                        options=["LOW", "MEDIUM", "HIGH"],
                        default=["LOW", "MEDIUM", "HIGH"],
                        key="planner_competition"
                    )
                
                with col3:
                    max_cpc = st.number_input(
                        "Max CPC ($)",
                        min_value=0.0,
                        value=float(df['cpc_high'].max()),
                        step=0.50,
                        key="planner_max_cpc"
                    )
                
                # Apply filters
                filtered_df = df[
                    (df['avg_monthly_searches'] >= min_searches) &
                    (df['competition'].isin(competition_filter)) &
                    (df['cpc_low'] <= max_cpc)
                ]
                
                st.write(f"Showing {len(filtered_df)} of {len(df)} keywords")
                
                # Display table
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    column_config={
                        "keyword": "Keyword",
                        "avg_monthly_searches": st.column_config.NumberColumn(
                            "Avg Monthly Searches",
                            format="%d"
                        ),
                        "competition": "Competition",
                        "cpc_low": st.column_config.NumberColumn(
                            "CPC Low",
                            format="$%.2f"
                        ),
                        "cpc_high": st.column_config.NumberColumn(
                            "CPC High",
                            format="$%.2f"
                        ),
                        "forecast_impressions": st.column_config.NumberColumn(
                            "Est. Impressions",
                            format="%.0f"
                        ),
                        "forecast_clicks": st.column_config.NumberColumn(
                            "Est. Clicks",
                            format="%.0f"
                        ),
                        "forecast_cost": st.column_config.NumberColumn(
                            "Est. Cost",
                            format="$%.2f"
                        )
                    }
                )
                
                # Export options
                st.subheader("💾 Export Keywords")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="keyword_ideas.csv",
                        mime="text/csv",
                        key="planner_download_csv"
                    )
                
                with col2:
                    if st.button("➕ Add to Campaign", key="planner_add_to_campaign"):
                        st.session_state['selected_keywords_for_campaign'] = filtered_df['keyword'].tolist()
                        st.success(f"Added {len(filtered_df)} keywords! Go to Campaign Wizard to create your campaign.")
                
            except Exception as e:
                st.error(f"Error fetching keyword data: {str(e)}")
                st.exception(e)
    
    # Display any previously saved keywords
    if st.session_state.get('selected_keywords_for_campaign'):
        st.markdown("---")
        st.subheader("📋 Selected Keywords for Campaign")
        st.write(f"{len(st.session_state['selected_keywords_for_campaign'])} keywords ready to add to campaign:")
        st.code('\n'.join(st.session_state['selected_keywords_for_campaign'][:20]))
        if st.button("Clear Selection", key="planner_clear_selection"):
            st.session_state['selected_keywords_for_campaign'] = []
            st.rerun()


# Alternative function name for backwards compatibility
def render_planner():
    """Alias for render_keyword_planner"""
    render_keyword_planner()