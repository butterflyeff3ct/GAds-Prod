# /app/components/keyword_manager.py
"""
Keyword Management Component
Functional UI for managing keywords with individual bids, status, and negatives.
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
    - Manage ad group negative keywords
    """
    
    ad_groups = config.get('ad_groups', [])
    if ad_group_index >= len(ad_groups):
        st.error("Invalid ad group index")
        return
    
    ad_group = ad_groups[ad_group_index]
    ag_name = ad_group.get('name', f'Ad Group {ad_group_index + 1}')
    
    st.subheader(f"📝 Keywords for {ag_name}")
    
    # Parse existing keywords
    keywords_text = ad_group.get('keywords', '')
    keyword_lines = [l.strip() for l in keywords_text.split('\n') if l.strip()]
    
    # Parse into structured format
    keywords_data = []
    for i, line in enumerate(keyword_lines):
        parts = line.rsplit(',', 2)  # Split from right: "keyword, match_type, bid"
        
        keyword_text = parts[0].strip()
        match_type = parts[1].strip() if len(parts) > 1 else "broad"
        bid = parts[2].strip() if len(parts) > 2 else ""
        
        keywords_data.append({
            'id': i,
            'keyword': keyword_text,
            'match_type': match_type,
            'bid': bid,
            'status': 'enabled'
        })
    
    # Display as editable table
    if keywords_data:
        st.write("**Current Keywords:**")
        
        # Create DataFrame for display
        df = pd.DataFrame(keywords_data)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "id": None,  # Hide ID
                "keyword": st.column_config.TextColumn("Keyword", required=True, width="large"),
                "match_type": st.column_config.SelectboxColumn(
                    "Match Type",
                    options=["exact", "phrase", "broad"],
                    required=True,
                    width="small"
                ),
                "bid": st.column_config.NumberColumn(
                    "Max CPC Bid ($)",
                    help="Leave empty to use ad group default",
                    min_value=0.01,
                    max_value=100.0,
                    format="$%.2f",
                    width="small"
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["enabled", "paused"],
                    required=True,
                    width="small"
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"keyword_editor_{ad_group_index}"
        )
        
        # Save changes back to config
        new_keywords_text = []
        for _, row in edited_df.iterrows():
            kw = row['keyword']
            mt = row['match_type']
            bid = row['bid']
            status = row['status']
            
            # Format: "keyword, match_type, bid, status"
            if pd.notna(bid) and bid != "":
                line = f"{kw}, {mt}, {bid}, {status}"
            else:
                line = f"{kw}, {mt}, , {status}"
            
            new_keywords_text.append(line)
        
        ad_group['keywords'] = '\n'.join(new_keywords_text)
    
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
    
    # Ad Group Negative Keywords
    st.markdown("---")
    st.subheader("🚫 Ad Group Negative Keywords")
    st.write("These keywords will prevent your ads from showing in this ad group")
    
    ag_negatives = ad_group.get('negative_keywords', [])
    if isinstance(ag_negatives, str):
        ag_negatives = [n.strip() for n in ag_negatives.split('\n') if n.strip()]
    
    ag_negatives_text = st.text_area(
        "Negative Keywords (one per line)",
        value='\n'.join(ag_negatives) if ag_negatives else '',
        placeholder='"free download"\ncheap alternative\n[competitor name]',
        help='Use "quotes" for phrase match, [brackets] for exact match',
        height=100,
        key=f"ag_negatives_{ad_group_index}"
    )
    
    ad_group['negative_keywords'] = [n.strip() for n in ag_negatives_text.split('\n') if n.strip()]


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
