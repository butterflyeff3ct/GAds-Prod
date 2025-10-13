"""
AI Ad Copy Generator Component
Generates headlines and descriptions using Gemini AI with proper character limits
"""

import streamlit as st
from typing import Dict, List


def render_ai_ad_generator(ad_group_index: int, config: dict):
    """
    Render AI-powered ad copy generation buttons
    
    Args:
        ad_group_index: Index of current ad group
        config: Campaign configuration
    """
    
    selected_ag = config['ad_groups'][ad_group_index]
    
    st.markdown("---")
    st.subheader("🤖 AI-Powered Ad Copy Generation")
    st.write("Let Gemini AI create headlines and descriptions based on your business")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Generate Headlines
        if st.button("✨ Generate Headlines", use_container_width=True, key=f"gen_headlines_{ad_group_index}"):
            with st.spinner("Generating headlines with Gemini AI..."):
                try:
                    from services.gemini_client import get_gemini_client
                    from app.quota_system import get_quota_manager
                    
                    gemini = get_gemini_client()
                    quota_mgr = get_quota_manager()
                    
                    # Get context from ad group and campaign
                    final_url = selected_ag.get('final_url', config.get('final_url', ''))
                    product_desc = config.get('product_description', '')
                    ad_group_name = selected_ag.get('name', 'Products')
                    
                    # Build context
                    context = f"Business: {final_url}\nProduct: {product_desc}\nAd Group: {ad_group_name}"
                    
                    if quota_mgr.can_use_gemini():
                        # Generate with real API
                        result = gemini.generate_ads(
                            prompt=context,
                            num_headlines=15,
                            num_descriptions=4,
                            tone="professional"
                        )
                        
                        headlines = result.get('headlines', [])
                        
                        # Ensure character limits (max 30 chars per headline)
                        headlines = [h[:30] for h in headlines]
                        
                        # Add to existing headlines
                        existing = selected_ag.get('headlines', [])
                        selected_ag['headlines'] = existing + headlines
                        
                        st.success(f"✅ Generated {len(headlines)} headlines!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Gemini quota exceeded. Using sample headlines.")
                        sample_headlines = _generate_sample_headlines(ad_group_name)
                        existing = selected_ag.get('headlines', [])
                        selected_ag['headlines'] = existing + sample_headlines
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Failed to generate headlines: {e}")
    
    with col2:
        # Generate Descriptions
        if st.button("✨ Generate Descriptions", use_container_width=True, key=f"gen_descriptions_{ad_group_index}"):
            with st.spinner("Generating descriptions with Gemini AI..."):
                try:
                    from services.gemini_client import get_gemini_client
                    from app.quota_system import get_quota_manager
                    
                    gemini = get_gemini_client()
                    quota_mgr = get_quota_manager()
                    
                    # Get context
                    final_url = selected_ag.get('final_url', config.get('final_url', ''))
                    product_desc = config.get('product_description', '')
                    ad_group_name = selected_ag.get('name', 'Products')
                    
                    context = f"Business: {final_url}\nProduct: {product_desc}\nAd Group: {ad_group_name}"
                    
                    if quota_mgr.can_use_gemini():
                        # Generate with real API
                        result = gemini.generate_ads(
                            prompt=context,
                            num_headlines=5,
                            num_descriptions=4,
                            tone="professional"
                        )
                        
                        descriptions = result.get('descriptions', [])
                        
                        # Ensure character limits (max 90 chars per description)
                        descriptions = [d[:90] for d in descriptions]
                        
                        # Add to existing descriptions
                        existing = selected_ag.get('descriptions', [])
                        selected_ag['descriptions'] = existing + descriptions
                        
                        st.success(f"✅ Generated {len(descriptions)} descriptions!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Gemini quota exceeded. Using sample descriptions.")
                        sample_descs = _generate_sample_descriptions(ad_group_name)
                        existing = selected_ag.get('descriptions', [])
                        selected_ag['descriptions'] = existing + sample_descs
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Failed to generate descriptions: {e}")
    
    # Info about character limits
    st.caption("📏 Headlines: Max 30 characters | Descriptions: Max 90 characters")
    st.caption("🤖 AI ensures all generated content meets Google Ads requirements")


def _generate_sample_headlines(ad_group_name: str) -> List[str]:
    """Generate sample headlines when API unavailable"""
    base = ad_group_name.replace("Ad Group", "Product").strip()
    
    return [
        f"Premium {base} Sale"[:30],
        "Free Shipping Today"[:30],
        "2-Year Warranty Included"[:30],
        "Top Rated by Experts"[:30],
        "Shop The Collection"[:30],
        "Limited Time Offer"[:30],
        "Best Price Guaranteed"[:30],
        "Order Now & Save"[:30],
        f"Quality {base}"[:30],
        f"Affordable {base}"[:30]
    ]


def _generate_sample_descriptions(ad_group_name: str) -> List[str]:
    """Generate sample descriptions when API unavailable"""
    base = ad_group_name.replace("Ad Group", "Product").strip()
    
    return [
        f"Discover our range of high-quality {base}. Fast, free shipping on all orders."[:90],
        f"Unbeatable prices on premium {base}. Click to see deals and save today."[:90],
        f"Engineered for performance. All products come with warranty and support."[:90],
        f"Shop the latest {base} collection. Trusted by thousands of customers."[:90]
    ]
