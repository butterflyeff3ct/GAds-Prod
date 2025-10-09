# /services/google_ads_client.py
import pandas as pd
from typing import List, Optional
import yaml
import os
import streamlit as st
from services.usage_manager import check_limit, record_usage

try:
    from google.ads.googleads.client import GoogleAdsClient
    from google.ads.googleads.errors import GoogleAdsException
    GOOGLE_ADS_API_AVAILABLE = True
except ImportError:
    GOOGLE_ADS_API_AVAILABLE = False

@st.cache_resource
def get_google_ads_client():
    """Initializes and returns a GoogleAdsKWPClient instance, caching it."""
    if not GOOGLE_ADS_API_AVAILABLE:
        return None
    try:
        return GoogleAdsKWPClient(config_path="config/config.yaml")
    except Exception as e:
        # Log the error but don't show it to the user to avoid confusion
        print(f"Google Ads API not available: {e}")
        return None

class GoogleAdsKWPClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)['google_ads']
        except Exception as e:
            print(f"Failed to load Google Ads config: {e}")
            raise e
        
        try:
            self.client = GoogleAdsClient.load_from_dict(self.config)
            self.customer_id = str(self.config['login_customer_id'])
            print("✅ Google Ads client initialized successfully.")
        except Exception as e:
            print(f"Google Ads API authentication failed: {e}")
            # Re-raise with a more specific message
            if "invalid_grant" in str(e):
                raise Exception("Google Ads API refresh token has expired. Please update your credentials or use mock data.")
            else:
                raise e

    def fetch_keyword_ideas(self, seed_keywords: List[str], location_ids: Optional[List[str]] = None) -> pd.DataFrame:
        # Check quota limits first
        within_limit, reason = check_limit("google_ads")
        if not within_limit:
            st.error(f"🚫 Google Ads API quota exceeded: {reason}")
            st.warning("Please try again later or contact administrator.")
            return pd.DataFrame()  # Return empty DataFrame
        
        if location_ids is None:
            location_ids = ["2840"]  # United States
        
        service = self.client.get_service("KeywordPlanIdeaService")
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = self.customer_id
        request.language = self.client.get_service("GoogleAdsService").language_constant_path("1000") # English
        for loc_id in location_ids:
            request.geo_target_constants.append(
                self.client.get_service("GoogleAdsService").geo_target_constant_path(loc_id)
            )
        request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
        request.keyword_seed.keywords.extend(seed_keywords)
        
        try:
            response = service.generate_keyword_ideas(request=request)
            
            # Record token usage (estimate based on keywords and results)
            tokens_used = len(seed_keywords) * 10 + len(response.results) * 5
            record_usage("google_ads", tokens_used)
            
            results = []
            for idea in response.results:
                metrics = idea.keyword_idea_metrics
                results.append({
                    "keyword": idea.text,
                    "avg_monthly_searches": metrics.avg_monthly_searches or 0,
                    "competition": str(metrics.competition.name),
                    "cpc_low": metrics.low_top_of_page_bid_micros / 1_000_000 if metrics.low_top_of_page_bid_micros else 0,
                    "cpc_high": metrics.high_top_of_page_bid_micros / 1_000_000 if metrics.high_top_of_page_bid_micros else 0,
                })
            return pd.DataFrame(results)
        except GoogleAdsException as ex:
            st.error(f"Google Ads API Error: {ex.failure.errors[0].message}")
            return pd.DataFrame()