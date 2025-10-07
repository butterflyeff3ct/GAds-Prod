# /app/search_terms_page.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.matching import MatchEngine

def render_search_terms_report():
    """
    Search Terms Report - Shows actual queries that triggered ads.
    This is one of the most valuable reports in Google Ads.
    """
    st.header("🔍 Search Terms Report")
    
    st.info("""
    **What is this report?**
    
    The Search Terms Report shows the actual search queries that triggered your ads.
    This helps you:
    - Discover new keyword opportunities
    - Find irrelevant queries to add as negative keywords
    - Understand how users actually search for your products
    """)
    
    df = st.session_state.get('simulation_results')
    if df is None or df.empty:
        st.warning("No data available. Run a simulation first.")
        return
    
    # Ensure we have query data
    if 'query' not in df.columns:
        st.error("Query data not available in simulation results.")
        return
    
    # Initialize match engine for analysis
    match_engine = MatchEngine()
    
    # ========== GENERATE SEARCH TERMS DATA ==========
    st.subheader("Search Terms Performance")
    
    # Aggregate by query
    search_terms_agg = df.groupby('query').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'cost': 'sum',
        'revenue': 'sum',
        'matched_keyword': 'first'  # Which keyword matched
    }).reset_index()
    
    # Calculate metrics
    search_terms_agg['ctr'] = (search_terms_agg['clicks'] / search_terms_agg['impressions'] * 100).fillna(0)
    search_terms_agg['cvr'] = (search_terms_agg['conversions'] / search_terms_agg['clicks'] * 100).fillna(0)
    search_terms_agg['cpc'] = (search_terms_agg['cost'] / search_terms_agg['clicks']).fillna(0)
    search_terms_agg['cpa'] = (search_terms_agg['cost'] / search_terms_agg['conversions']).fillna(0)
    search_terms_agg['roas'] = (search_terms_agg['revenue'] / search_terms_agg['cost']).fillna(0)
    
    # ========== FILTERS ==========
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_impressions = st.number_input(
            "Min Impressions",
            min_value=0,
            value=0,
            step=10,
            key="st_min_impressions"
        )
    
    with col2:
        performance_filter = st.selectbox(
            "Performance Filter",
            ["All", "High CTR (>3%)", "Low CTR (<1%)", "High CVR (>2%)", "Low CVR (<0.5%)", "No Conversions"],
            key="st_performance_filter"
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort By",
            ["impressions", "clicks", "conversions", "cost", "ctr", "cvr", "roas"],
            index=1,  # Default to clicks
            key="st_sort_by"
        )
    
    # Apply filters
    filtered_df = search_terms_agg[search_terms_agg['impressions'] >= min_impressions]
    
    if performance_filter == "High CTR (>3%)":
        filtered_df = filtered_df[filtered_df['ctr'] > 3.0]
    elif performance_filter == "Low CTR (<1%)":
        filtered_df = filtered_df[filtered_df['ctr'] < 1.0]
    elif performance_filter == "High CVR (>2%)":
        filtered_df = filtered_df[filtered_df['cvr'] > 2.0]
    elif performance_filter == "Low CVR (<0.5%)":
        filtered_df = filtered_df[filtered_df['cvr'] < 0.5]
    elif performance_filter == "No Conversions":
        filtered_df = filtered_df[filtered_df['conversions'] == 0]
    
    filtered_df = filtered_df.sort_values(sort_by, ascending=False)
    
    st.write(f"Showing {len(filtered_df)} of {len(search_terms_agg)} search terms")
    
    # ========== MAIN TABLE ==========
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config={
            "query": st.column_config.TextColumn("Search Term", width="medium"),
            "matched_keyword": st.column_config.TextColumn("Matched Keyword", width="medium"),
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
    
    # ========== INSIGHTS ==========
    st.markdown("---")
    st.subheader("💡 Insights & Recommendations")
    
    tab1, tab2, tab3, tab4 = st.tabs(["New Keywords", "Negative Keywords", "Match Type Analysis", "Query Analysis"])
    
    with tab1:
        st.write("**High-performing search terms to add as keywords:**")
        
        # Find terms not already in keyword list
        if 'matched_keyword' in filtered_df.columns:
            # High CTR or high conversions but not exact keyword match
            new_keyword_candidates = filtered_df[
                ((filtered_df['ctr'] > 3.0) | (filtered_df['conversions'] > 2)) &
                (filtered_df['query'] != filtered_df['matched_keyword'])
            ].head(10)
            
            if not new_keyword_candidates.empty:
                for _, row in new_keyword_candidates.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{row['query']}**")
                        st.caption(f"Matched: {row['matched_keyword']} | CTR: {row['ctr']:.2f}% | Conv: {int(row['conversions'])}")
                    with col2:
                        if st.button("Add as Keyword", key=f"add_kw_{row['query']}"):
                            st.success(f"Would add '{row['query']}' as keyword")
            else:
                st.info("No new keyword opportunities found with current filters")
    
    with tab2:
        st.write("**Poor-performing search terms to add as negative keywords:**")
        
        # Low CTR or high cost with no conversions
        negative_candidates = filtered_df[
            ((filtered_df['ctr'] < 0.5) | 
             ((filtered_df['conversions'] == 0) & (filtered_df['cost'] > 5)))
        ].head(10)
        
        if not negative_candidates.empty:
            for _, row in negative_candidates.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{row['query']}**")
                    st.caption(f"CTR: {row['ctr']:.2f}% | Cost: ${row['cost']:.2f} | Conv: {int(row['conversions'])}")
                with col2:
                    if st.button("Add as Negative", key=f"add_neg_{row['query']}"):
                        st.success(f"Would add '{row['query']}' as negative keyword")
        else:
            st.info("No obvious negative keyword candidates found")
    
    with tab3:
        st.write("**Match Type Performance Analysis**")
        
        # Analyze how well each match type is working
        if 'matched_keyword' in df.columns and 'match_type' in df.columns:
            match_type_perf = df.groupby('match_type').agg({
                'query': 'count',
                'clicks': 'sum',
                'conversions': 'sum',
                'cost': 'sum'
            }).reset_index()
            
            match_type_perf.columns = ['Match Type', 'Queries', 'Clicks', 'Conversions', 'Cost']
            match_type_perf['Avg CPA'] = (match_type_perf['Cost'] / match_type_perf['Conversions']).fillna(0)
            
            st.dataframe(match_type_perf, use_container_width=True, hide_index=True)
            
            # Recommendations
            st.write("**Recommendations:**")
            for _, row in match_type_perf.iterrows():
                match_type = row['Match Type']
                if row['Conversions'] == 0 and row['Cost'] > 10:
                    st.warning(f"⚠️ {match_type.title()} match is spending without conversions - consider narrowing")
                elif row['Avg CPA'] > 0 and row['Avg CPA'] < 20:
                    st.success(f"✅ {match_type.title()} match is performing well (CPA: ${row['Avg CPA']:.2f})")
        else:
            st.info("Match type data not available")
    
    with tab4:
        st.write("**Query Pattern Analysis**")
        
        # Analyze query characteristics
        search_terms_agg['query_length'] = search_terms_agg['query'].str.split().str.len()
        
        # Query length impact
        length_analysis = search_terms_agg.groupby('query_length').agg({
            'impressions': 'sum',
            'clicks': 'sum',
            'conversions': 'sum',
            'cost': 'sum'
        }).reset_index()
        
        length_analysis['ctr'] = (length_analysis['clicks'] / length_analysis['impressions'] * 100).fillna(0)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=length_analysis['query_length'],
            y=length_analysis['ctr'],
            name='CTR by Query Length',
            marker_color='#4285F4'
        ))
        
        fig.update_layout(
            title='CTR by Query Length (number of words)',
            xaxis_title='Query Length (words)',
            yaxis_title='CTR (%)',
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Common query patterns
        st.write("**Common Query Patterns:**")
        
        # Find queries with modifiers
        modifier_patterns = {
            'Questions': ['how', 'what', 'where', 'when', 'why'],
            'Commercial': ['buy', 'purchase', 'order', 'price', 'cost'],
            'Research': ['best', 'top', 'review', 'compare'],
            'Local': ['near me', 'nearby', 'local']
        }
        
        pattern_stats = {}
        for pattern_name, keywords in modifier_patterns.items():
            matching_queries = search_terms_agg[
                search_terms_agg['query'].str.contains('|'.join(keywords), case=False, na=False)
            ]
            if not matching_queries.empty:
                pattern_stats[pattern_name] = {
                    'count': len(matching_queries),
                    'clicks': matching_queries['clicks'].sum(),
                    'conversions': matching_queries['conversions'].sum(),
                    'avg_ctr': matching_queries['ctr'].mean()
                }
        
        if pattern_stats:
            pattern_df = pd.DataFrame(pattern_stats).T
            st.dataframe(pattern_df, use_container_width=True)
    
    # ========== EXPORT ==========
    st.markdown("---")
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Export Search Terms Report",
        data=csv,
        file_name="search_terms_report.csv",
        mime="text/csv"
    )
    
    # ========== EDUCATIONAL NOTE ==========
    with st.expander("📚 Learn More About Search Terms"):
        st.markdown("""
        ### Why is the Search Terms Report Important?
        
        **1. Discover New Keywords**
        - See actual phrases people use to find your ads
        - High-performing search terms can become new keywords
        - Better targeting = better ROI
        
        **2. Find Negative Keywords**
        - Identify irrelevant searches wasting budget
        - Add them as negatives to prevent future waste
        - Improve campaign efficiency
        
        **3. Understand User Intent**
        - See how people search for your products/services
        - Adjust ad copy to match search intent
        - Improve Quality Score with better relevance
        
        **4. Optimize Match Types**
        - See if broad match is too broad
        - Check if phrase match captures right queries
        - Balance reach vs relevance
        
        ### Best Practices:
        - Review this report weekly
        - Add 5-10 negative keywords per review
        - Test high-performing terms as exact match keywords
        - Look for patterns in converting vs non-converting queries
        """)
