"""
Keyword Enrichment Service
Combines Gemini AI keyword generation with Google Ads API metrics

Flow:
1. Gemini generates creative keywords (using URL + description)
2. Google Ads API enriches with real metrics (volume, CPC, competition)
3. Returns enriched keyword data for display
"""

import streamlit as st
from typing import List, Dict
import pandas as pd
import logging

logger = logging.getLogger('keyword_enrichment')


def generate_and_enrich_keywords(
    product_description: str,
    final_url: str = None,
    location_ids: List[str] = None
) -> pd.DataFrame:
    """
    Complete keyword generation and enrichment flow
    
    Args:
        product_description: Description of product/service
        final_url: Business website URL (optional, improves context)
        location_ids: Target location IDs for metrics
        
    Returns:
        DataFrame with enriched keywords (text, match_type, search_volume, CPC, competition)
    """
    from services.gemini_client import get_gemini_client
    from services.google_ads_client import get_google_ads_client
    from app.quota_system import get_quota_manager
    
    quota_mgr = get_quota_manager()
    
    # STEP 1: Generate keywords with Gemini (enhanced with URL context)
    st.info("🤖 Step 1: Generating keywords with Gemini AI...")
    
    gemini_client = get_gemini_client()
    
    # Enhanced keyword generation using URL + description
    if gemini_client and quota_mgr.can_use_gemini():
        try:
            # Build enhanced prompt
            if final_url:
                full_prompt = f"""
                Act as a Google Ads specialist. Generate 20 highly relevant keywords for this business.
                
                Business Website: {final_url}
                Product/Service Description: "{product_description}"
                
                Analyze the business type, industry, and target audience from the URL and description.
                
                Generate 20 keywords including:
                - 5 high-intent commercial keywords (buyers ready to purchase)
                - 5 long-tail keywords (3-5 words, very specific)
                - 5 informational keywords (research/learning phase)
                - 5 brand/competitor comparison keywords
                
                Consider the industry context and business model.
                
                Return ONLY comma-separated keywords, no formatting, no explanations.
                """
            else:
                full_prompt = f"""
                Act as a Google Ads specialist. Based on the product description, generate 20 relevant keywords.
                
                Product: "{product_description}"
                
                Include:
                - 5 high-intent commercial keywords
                - 5 long-tail keywords (3-5 words)
                - 5 informational keywords
                - 5 competitor/comparison keywords
                
                Return ONLY comma-separated keywords, no formatting.
                """
            
            response = gemini_client.model.generate_content(full_prompt)
            quota_mgr.increment_gemini_tokens(500)
            
            keywords = response.text.strip().split(",")
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            
            st.success(f"✅ Generated {len(keywords)} keywords with Gemini AI")
            
        except Exception as e:
            st.warning(f"⚠️ Gemini API failed: {e}")
            st.info("💡 Using mock keywords")
            keywords = gemini_client._generate_mock_keywords(product_description)
    else:
        st.info("💡 Using mock keywords (quota exceeded or API unavailable)")
        keywords = _generate_simple_mock_keywords(product_description)
    
    # STEP 2: Enrich with Google Ads API metrics
    st.info("🔍 Step 2: Fetching real metrics from Google Ads API...")
    
    ads_client = get_google_ads_client()
    
    if ads_client and quota_mgr.can_use_google_ads():
        try:
            # Fetch keyword metrics from Google Ads API
            keyword_data = ads_client.fetch_keyword_ideas(
                seed_keywords=keywords[:20],  # Limit to 20 for API call
                location_ids=location_ids or ["2840"]
            )
            
            # Increment quota
            quota_mgr.increment_google_ads_ops(1)
            
            if not keyword_data.empty:
                # Add match_type and status columns
                keyword_data['match_type'] = 'broad'
                keyword_data['status'] = 'enabled'
                keyword_data['max_cpc_bid'] = None
                
                st.success(f"✅ Enriched {len(keyword_data)} keywords with Google Ads metrics")
                return keyword_data
            else:
                st.warning("⚠️ Google Ads API returned no data")
                return _create_mock_enriched_keywords(keywords)
                
        except Exception as e:
            st.error(f"❌ Google Ads API failed: {e}")
            st.info("💡 Using mock metrics")
            return _create_mock_enriched_keywords(keywords)
    else:
        st.info("💡 Using mock metrics (quota exceeded or API unavailable)")
        return _create_mock_enriched_keywords(keywords)


def _generate_simple_mock_keywords(prompt: str) -> List[str]:
    """Simple mock keywords when Gemini unavailable"""
    base = "product"
    if "AI" in prompt or "artificial intelligence" in prompt.lower():
        base = "AI solution"
    elif "battery" in prompt.lower():
        base = "battery"
    
    return [
        f"{base}", f"buy {base}", f"best {base}", f"{base} for sale",
        f"{base} online", f"cheap {base}", f"{base} deals", f"top {base}",
        f"{base} reviews", f"{base} comparison", f"affordable {base}",
        f"{base} near me", f"premium {base}", f"{base} store",
        f"{base} supplier", f"{base} manufacturer", f"{base} service",
        f"{base} provider", f"{base} company", f"{base} expert"
    ]


def _create_mock_enriched_keywords(keywords: List[str]) -> pd.DataFrame:
    """
    Create mock enriched keyword data when Google Ads API unavailable
    
    Args:
        keywords: List of keyword strings
        
    Returns:
        DataFrame with mock metrics
    """
    import random
    
    enriched_keywords = []
    
    for keyword in keywords:
        # Generate realistic mock metrics
        keyword_length = len(keyword.split())
        
        # Longer keywords typically have lower volume but better conversion
        if keyword_length >= 4:
            # Long-tail keyword
            volume = random.randint(100, 1000)
            competition = random.choice(["LOW", "MEDIUM"])
            cpc_low = round(random.uniform(0.50, 1.50), 2)
            cpc_high = round(random.uniform(1.50, 3.00), 2)
        elif keyword_length >= 2:
            # Medium keyword
            volume = random.randint(1000, 10000)
            competition = random.choice(["MEDIUM", "HIGH"])
            cpc_low = round(random.uniform(1.00, 2.50), 2)
            cpc_high = round(random.uniform(2.50, 5.00), 2)
        else:
            # Short, broad keyword
            volume = random.randint(5000, 50000)
            competition = "HIGH"
            cpc_low = round(random.uniform(2.00, 4.00), 2)
            cpc_high = round(random.uniform(4.00, 8.00), 2)
        
        enriched_keywords.append({
            'keyword': keyword,
            'avg_monthly_searches': volume,
            'competition': competition,
            'cpc_low': cpc_low,
            'cpc_high': cpc_high,
            'match_type': 'broad',
            'status': 'enabled',
            'max_cpc_bid': None
        })
    
    return pd.DataFrame(enriched_keywords)


def enrich_existing_keywords(keywords_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich existing keywords with Google Ads metrics
    Used when user already has keywords and wants to add metrics
    
    Args:
        keywords_df: DataFrame with keyword column
        
    Returns:
        DataFrame with added metrics
    """
    from services.google_ads_client import get_google_ads_client
    from app.quota_system import get_quota_manager
    
    quota_mgr = get_quota_manager()
    ads_client = get_google_ads_client()
    
    if ads_client and quota_mgr.can_use_google_ads():
        try:
            # Extract keyword list
            keyword_list = keywords_df['keyword'].tolist()
            
            # Fetch metrics
            metrics_df = ads_client.fetch_keyword_ideas(
                seed_keywords=keyword_list[:20],  # Limit to 20
                location_ids=["2840"]
            )
            
            quota_mgr.increment_google_ads_ops(1)
            
            # Merge with existing data
            return keywords_df.merge(
                metrics_df,
                on='keyword',
                how='left'
            ).fillna(0)
            
        except Exception as e:
            logger.error(f"Failed to enrich keywords: {e}")
            return _create_mock_enriched_keywords(keyword_list)
    else:
        # Use mock data
        keyword_list = keywords_df['keyword'].tolist()
        return _create_mock_enriched_keywords(keyword_list)
