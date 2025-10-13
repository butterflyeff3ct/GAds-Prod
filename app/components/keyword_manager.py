# /app/components/keyword_manager.py
"""
Keyword Management Component - ENHANCED
Functional UI for managing keywords with Google Ads API metrics
"""

import streamlit as st
import pandas as pd
from typing import List, Dict

def render_keyword_manager(ad_group_index: int, config: Dict):
    """
    Render keyword management interface for an ad group.
    
    Features:
    - Add/edit/remove keywords
    - Set individual keyword bids
    - Set match types
    - Display Google Ads metrics (search volume, CPC, competition)
    """
    
    ad_groups = config.get('ad_groups', [])
    if ad_group_index >= len(ad_groups):
        st.error("Invalid ad group index")
        return
    
    ad_group = ad_groups[ad_group_index]
    ag_name = ad_group.get('name', f'Ad Group {ad_group_index + 1}')
    
    st.subheader(f"📝 Keywords for {ag_name}")
    
    # Check if we have enriched keyword data
    has_metrics = 'keywords_data' in ad_group and ad_group['keywords_data']
    
    # Parse existing keywords
    keywords_text = ad_group.get('keywords', '')
    keyword_lines = [l.strip() for l in keywords_text.split('\n') if l.strip()]
    
    # Parse into structured format
    keywords_data = []
    
    if has_metrics:
        # Use enriched data with Google Ads metrics
        enriched_data = ad_group['keywords_data']
        
        for i, kw_data in enumerate(enriched_data):
            keywords_data.append({
                'id': i,
                'keyword': kw_data.get('keyword', ''),
                'match_type': kw_data.get('match_type', 'broad'),
                'avg_monthly_searches': kw_data.get('avg_monthly_searches', 0),
                'competition': kw_data.get('competition', 'N/A'),
                'cpc_low': kw_data.get('cpc_low', 0),
                'cpc_high': kw_data.get('cpc_high', 0),
                'bid': kw_data.get('max_cpc_bid', ''),
                'status': kw_data.get('status', 'enabled')
            })
    else:
        # Fallback: Parse from text format (no metrics)
        for i, line in enumerate(keyword_lines):
            parts = [p.strip() for p in line.split(',')]
            
            keyword_text = parts[0] if len(parts) > 0 else ""
            match_type = parts[1] if len(parts) > 1 else "broad"
            bid = parts[2] if len(parts) > 2 else ""
            status = parts[3] if len(parts) > 3 else "enabled"
            
            keywords_data.append({
                'id': i,
                'keyword': keyword_text,
                'match_type': match_type,
                'avg_monthly_searches': 0,
                'competition': 'N/A',
                'cpc_low': 0,
                'cpc_high': 0,
                'bid': bid,
                'status': status
            })
    
    # Display as editable table
    if keywords_data:
        st.write("**Current Keywords:**")
        
        # Add button to enrich with Google Ads API if not already enriched
        if not has_metrics:
            if st.button("🔍 Fetch Google Ads Metrics", key=f"enrich_kw_{ad_group_index}", help="Get search volume, CPC, and competition data"):
                with st.spinner("Fetching metrics from Google Ads API..."):
                    try:
                        from services.google_ads_client import get_google_ads_client
                        from app.quota_system import get_quota_manager
                        
                        quota_mgr = get_quota_manager()
                        ads_client = get_google_ads_client()
                        
                        if ads_client and quota_mgr.can_use_google_ads():
                            # Extract keyword texts
                            kw_list = [k['keyword'] for k in keywords_data]
                            
                            # Fetch metrics
                            metrics_df = ads_client.fetch_keyword_ideas(
                                seed_keywords=kw_list[:20],
                                location_ids=["2840"]
                            )
                            
                            quota_mgr.increment_google_ads_ops(1)
                            
                            # Merge metrics with keywords
                            enriched_data = []
                            for kw in keywords_data:
                                # Find matching row in metrics
                                match = metrics_df[metrics_df['keyword'] == kw['keyword']]
                                
                                if not match.empty:
                                    row = match.iloc[0]
                                    kw['avg_monthly_searches'] = int(row['avg_monthly_searches'])
                                    kw['competition'] = row['competition']
                                    kw['cpc_low'] = float(row['cpc_low'])
                                    kw['cpc_high'] = float(row['cpc_high'])
                                
                                enriched_data.append(kw)
                            
                            # Store enriched data
                            ad_group['keywords_data'] = enriched_data
                            
                            st.success("✅ Metrics fetched successfully!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Google Ads API quota exceeded. Using mock metrics.")
                            # Generate mock metrics
                            import random
                            for kw in keywords_data:
                                kw['avg_monthly_searches'] = random.randint(100, 10000)
                                kw['competition'] = random.choice(['LOW', 'MEDIUM', 'HIGH'])
                                kw['cpc_low'] = round(random.uniform(0.5, 2.5), 2)
                                kw['cpc_high'] = round(random.uniform(2.5, 5.0), 2)
                            
                            ad_group['keywords_data'] = keywords_data
                            st.success("✅ Mock metrics generated!")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Failed to fetch metrics: {e}")
        
        # Create DataFrame for display
        df = pd.DataFrame(keywords_data)
        
        # Configure columns
        column_config = {
            "id": None,  # Hide ID
            "keyword": st.column_config.TextColumn("Keyword", required=True, width="medium"),
            "match_type": st.column_config.SelectboxColumn(
                "Match Type",
                options=["exact", "phrase", "broad"],
                required=True,
                width="small"
            )
        }
        
        # Add metrics columns if available
        if has_metrics or (df['avg_monthly_searches'] > 0).any():
            column_config["avg_monthly_searches"] = st.column_config.NumberColumn(
                "Monthly Searches",
                help="Average monthly search volume",
                format="%d",
                width="small"
            )
            column_config["competition"] = st.column_config.TextColumn(
                "Competition",
                width="small"
            )
            column_config["cpc_low"] = st.column_config.NumberColumn(
                "CPC Low",
                help="Low range CPC",
                format="$%.2f",
                width="small"
            )
            column_config["cpc_high"] = st.column_config.NumberColumn(
                "CPC High",
                help="High range CPC",
                format="$%.2f",
                width="small"
            )
        
        # Always show bid and status
        column_config["bid"] = st.column_config.NumberColumn(
            "Max CPC Bid ($)",
            help="Leave empty to use ad group default",
            min_value=0.01,
            max_value=100.0,
            format="$%.2f",
            width="small"
        )
        column_config["status"] = st.column_config.SelectboxColumn(
            "Status",
            options=["enabled", "paused"],
            required=True,
            width="small"
        )
        
        edited_df = st.data_editor(
            df,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key=f"keyword_editor_{ad_group_index}",
            hide_index=True
        )
        
        # Save changes back to config
        new_keywords_text = []
        updated_enriched_data = []
        
        for _, row in edited_df.iterrows():
            kw = row['keyword']
            mt = row['match_type']
            bid = row['bid']
            status = row['status']
            
            # Format for text storage: "keyword, match_type, bid, status"
            if pd.notna(bid) and bid != "":
                line = f"{kw}, {mt}, {bid}, {status}"
            else:
                line = f"{kw}, {mt}, , {status}"
            
            new_keywords_text.append(line)
            
            # Preserve enriched data if available
            if has_metrics:
                updated_enriched_data.append({
                    'keyword': kw,
                    'match_type': mt,
                    'avg_monthly_searches': int(row['avg_monthly_searches']) if 'avg_monthly_searches' in row else 0,
                    'competition': row['competition'] if 'competition' in row else 'N/A',
                    'cpc_low': float(row['cpc_low']) if 'cpc_low' in row else 0,
                    'cpc_high': float(row['cpc_high']) if 'cpc_high' in row else 0,
                    'max_cpc_bid': bid,
                    'status': status
                })
        
        ad_group['keywords'] = '\n'.join(new_keywords_text)
        if has_metrics:
            ad_group['keywords_data'] = updated_enriched_data
    
    else:
        st.info("No keywords yet. Add keywords below.")
    
    # Quick add section
    with st.expander("➕ Quick Add Keywords", expanded=not keywords_data):
        st.write("Add multiple keywords at once (one per line)")
        
        bulk_add = st.text_area(
            "Keywords",
            placeholder="running shoes\nbest athletic footwear\nbuy sneakers online",
            height=100,
            key=f"bulk_add_{ad_group_index}"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            default_match = st.selectbox(
                "Default Match Type",
                ["broad", "phrase", "exact"],
                key=f"default_match_{ad_group_index}"
            )
        with col2:
            use_default_bid = st.checkbox(
                "Use ad group default bid",
                value=True,
                key=f"use_default_{ad_group_index}"
            )
        with col3:
            if not use_default_bid:
                default_bid = st.number_input(
                    "Default Bid ($)",
                    min_value=0.01,
                    value=1.50,
                    step=0.10,
                    key=f"default_bid_{ad_group_index}"
                )
        
        if st.button("Add Keywords", key=f"add_kw_btn_{ad_group_index}"):
            if bulk_add.strip():
                new_lines = bulk_add.strip().split('\n')
                existing_keywords = ad_group.get('keywords', '')
                
                for new_kw in new_lines:
                    new_kw = new_kw.strip()
                    if new_kw:
                        if use_default_bid:
                            line = f"{new_kw}, {default_match}, , enabled"
                        else:
                            line = f"{new_kw}, {default_match}, {default_bid}, enabled"
                        
                        existing_keywords += f"\n{line}"
                
                ad_group['keywords'] = existing_keywords.strip()
                st.success(f"Added {len(new_lines)} keywords!")
                st.rerun()


def render_campaign_negative_keywords(config: Dict):
    """
    Render campaign-level negative keywords.
    These apply to ALL ad groups in the campaign.
    """
    
    st.subheader("🚫 Campaign Negative Keywords")
    st.write("Apply to all ad groups in this campaign")
    
    campaign_negatives = config.get('negative_keywords', [])
    if isinstance(campaign_negatives, str):
        campaign_negatives = [n.strip() for n in campaign_negatives.split('\n') if n.strip()]
    
    negatives_text = st.text_area(
        "Campaign Negative Keywords",
        value='\n'.join(campaign_negatives) if campaign_negatives else '',
        placeholder='free\ncheap\n"competitor brand"\n[exact competitor name]',
        help='Prevents ads from showing for these searches across ALL ad groups',
        height=120,
        key="campaign_negatives"
    )
    
    config['negative_keywords'] = [n.strip() for n in negatives_text.split('\n') if n.strip()]
    
    if config.get('negative_keywords'):
        st.info(f"✅ {len(config['negative_keywords'])} campaign-level negative keywords active")
