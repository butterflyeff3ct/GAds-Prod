# /services/google_ads_client.py - OPTIMIZED VERSION
# Improved caching and lazy loading for faster startup

import pandas as pd
from typing import List, Optional
import yaml
import os
import streamlit as st
import logging
import re

# Get logger for Google Ads API
logger = logging.getLogger('google_ads_api')

# Track initialization
_init_logged = False
_api_available_checked = False
_GOOGLE_ADS_API_AVAILABLE = None

# ========================================
# LAZY CHECKING FOR API AVAILABILITY
# ========================================

def check_google_ads_api_availability():
    """Check if Google Ads API is available - cached result"""
    global _api_available_checked, _GOOGLE_ADS_API_AVAILABLE
    
    if not _api_available_checked:
        try:
            from google.ads.googleads.client import GoogleAdsClient
            from google.ads.googleads.errors import GoogleAdsException
            _GOOGLE_ADS_API_AVAILABLE = True
        except ImportError:
            _GOOGLE_ADS_API_AVAILABLE = False
        finally:
            _api_available_checked = True
    
    return _GOOGLE_ADS_API_AVAILABLE

# Public constant that checks lazily
@property
def GOOGLE_ADS_API_AVAILABLE():
    return check_google_ads_api_availability()

# For backward compatibility
GOOGLE_ADS_API_AVAILABLE = check_google_ads_api_availability()

# ========================================
# OPTIMIZED CLIENT INITIALIZATION
# ========================================

@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_google_ads_client():
    """
    Initializes and returns a GoogleAdsKWPClient instance with caching.
    TTL of 1 hour prevents stale tokens while reducing initialization overhead.
    """
    global _init_logged
    
    if not check_google_ads_api_availability():
        if not _init_logged:
            logger.info("ℹ️ Google Ads API: Not available (using mock)")
            _init_logged = True
        return None
    
    try:
        return GoogleAdsKWPClient(config_path="config/config.yaml")
    except Exception as e:
        if not _init_logged:
            if "invalid_grant" in str(e) or "expired" in str(e):
                logger.error("❌ Google Ads API: Token expired")
            else:
                logger.error("❌ Google Ads API: Failed")
            _init_logged = True
        return None

# ========================================
# MAIN CLIENT CLASS
# ========================================

class GoogleAdsKWPClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        global _init_logged
        
        # Lazy import Google Ads modules
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)['google_ads']
        except Exception as e:
            raise e
        
        try:
            self.client = GoogleAdsClient.load_from_dict(self.config)
            self.customer_id = str(self.config['login_customer_id'])
            
            # Only log once
            if not _init_logged:
                logger.info("✅ Google Ads API: Connected")
                _init_logged = True
        except Exception as e:
            if not _init_logged:
                if "invalid_grant" in str(e):
                    logger.error("❌ Google Ads API: Token expired")
                else:
                    logger.error("❌ Google Ads API: Failed")
                _init_logged = True
            
            # Re-raise with message
            if "invalid_grant" in str(e):
                raise Exception("Google Ads API refresh token has expired.")
            else:
                raise e

    def fetch_keyword_ideas(self, seed_keywords: List[str], location_ids: Optional[List[str]] = None) -> pd.DataFrame:
        # NEW: Check quota before using API
        from app.quota_system import get_quota_manager
        quota_mgr = get_quota_manager()
        
        if not quota_mgr.can_use_google_ads():
            st.info("💡 Using mock data (Google Ads API quota exceeded)")
            return self._generate_mock_keyword_data(seed_keywords)
        
        if location_ids is None:
            location_ids = ["2840"]  # United States
        
        # Lazy import GoogleAdsException
        from google.ads.googleads.errors import GoogleAdsException
        
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
            
            # NEW: Increment operation count
            quota_mgr.increment_google_ads_ops(1)
            
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
    
    def fetch_keyword_ideas_from_url(self, url: str, description: str = None, location_ids: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Generate keyword ideas from URL + description using Google Ads API.
        This is the PRIMARY method for keyword generation in the wizard.
        
        Args:
            url: The business website URL
            description: Optional product/service description
            location_ids: Geographic locations (default: United States)
        
        Returns:
            DataFrame with columns: keyword, avg_monthly_searches, competition, cpc_low, cpc_high
        
        Cost: 1 Google Ads operation
        """
        from app.quota_system import get_quota_manager
        quota_mgr = get_quota_manager()
        
        if not quota_mgr.can_use_google_ads():
            st.info("💡 Using mock data (Google Ads API quota exceeded)")
            # Generate seed keywords from description for mock
            seed_kws = self._extract_keywords_from_text(description or url)
            return self._generate_mock_keyword_data(seed_kws)
        
        if location_ids is None:
            location_ids = ["2840"]  # United States
        
        # Lazy import GoogleAdsException
        from google.ads.googleads.errors import GoogleAdsException
        
        try:
            service = self.client.get_service("KeywordPlanIdeaService")
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            
            # Set language
            request.language = self.client.get_service("GoogleAdsService").language_constant_path("1000")  # English
            
            # Set locations
            for loc_id in location_ids:
                request.geo_target_constants.append(
                    self.client.get_service("GoogleAdsService").geo_target_constant_path(loc_id)
                )
            
            # Set network
            request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
            
            # Use URL seed (PRIMARY input)
            request.url_seed.url = url
            
            # Execute request
            response = service.generate_keyword_ideas(request=request)
            
            # Increment quota
            quota_mgr.increment_google_ads_ops(1)
            
            # Parse results
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
            
            # Sort by search volume (descending)
            df = pd.DataFrame(results)
            if not df.empty:
                df = df.sort_values('avg_monthly_searches', ascending=False).reset_index(drop=True)
            
            return df
            
        except GoogleAdsException as ex:
            error_msg = ex.failure.errors[0].message if ex.failure.errors else str(ex)
            st.error(f"Google Ads API Error: {error_msg}")
            
            # Fallback to mock data
            seed_kws = self._extract_keywords_from_text(description or url)
            return self._generate_mock_keyword_data(seed_kws)
        except Exception as e:
            st.error(f"Keyword generation error: {str(e)}")
            seed_kws = self._extract_keywords_from_text(description or url)
            return self._generate_mock_keyword_data(seed_kws)
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract potential keywords from text for mock generation."""
        # Remove URLs, special chars
        text = re.sub(r'https?://\S+', '', text.lower())
        text = re.sub(r'[^a-z\s]', ' ', text)
        
        # Extract words 3+ chars
        words = [w.strip() for w in text.split() if len(w.strip()) >= 3]
        
        # Remove common stop words
        stop_words = {'the', 'and', 'for', 'are', 'with', 'this', 'that', 'from', 'have', 'was', 'were'}
        keywords = [w for w in words if w not in stop_words]
        
        # Return top unique words
        return list(dict.fromkeys(keywords))[:5]
    
    @staticmethod
    @st.cache_data(ttl=300)  # Cache mock data for 5 minutes
    def _generate_mock_keyword_data(seed_keywords: List[str]) -> pd.DataFrame:
        """Generate realistic mock keyword data when quota exceeded - CACHED"""
        import random
        
        results = []
        for keyword in seed_keywords:
            # Generate variations
            variations = [
                keyword,
                f"buy {keyword}",
                f"best {keyword}",
                f"{keyword} near me",
                f"{keyword} online"
            ]
            
            for var in variations[:3]:  # Limit to avoid too much mock data
                results.append({
                    "keyword": var,
                    "avg_monthly_searches": random.randint(100, 10000),
                    "competition": random.choice(["LOW", "MEDIUM", "HIGH"]),
                    "cpc_low": round(random.uniform(0.5, 2.0), 2),
                    "cpc_high": round(random.uniform(2.0, 5.0), 2),
                })
        
        return pd.DataFrame(results)
