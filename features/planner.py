# /features/planner.py
import pandas as pd
from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from services.google_ads_client import get_google_ads_client, GOOGLE_ADS_API_AVAILABLE
import streamlit as st

class KWPSource(Enum):
    GOOGLE_ADS_API = "google_ads_api"
    MOCK = "mock"

@dataclass
class KeywordMetrics:
    keyword: str
    avg_monthly_searches: int
    competition: str
    cpc_low: float
    cpc_high: float
    quality_score: float = 7.0
    
    @property
    def daily_searches(self) -> float:
        """Convert monthly searches to daily average."""
        return self.avg_monthly_searches / 30.4
    
    @property
    def expected_ctr(self) -> float:
        """
        Expected CTR based on competition level.
        High competition = lower CTR (more ads competing)
        """
        competition_ctr = {
            "LOW": 0.055,
            "MEDIUM": 0.040,
            "HIGH": 0.028,
            "UNSPECIFIED": 0.035
        }
        return competition_ctr.get(self.competition, 0.035)

    @property
    def expected_cvr(self) -> float:
        """
        Expected conversion rate based on competition.
        High competition keywords often convert better (higher intent).
        """
        competition_cvr = {
            "LOW": 0.018,
            "MEDIUM": 0.025,
            "HIGH": 0.032,
            "UNSPECIFIED": 0.022
        }
        return competition_cvr.get(self.competition, 0.022)

def fetch_keyword_data(seed_keywords: List[str], source: KWPSource, 
                       location_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Fetch keyword data from either Google Ads API or generate mock data.
    
    Args:
        seed_keywords: List of seed keywords to get ideas for
        source: KWPSource.GOOGLE_ADS_API or KWPSource.MOCK
        location_ids: List of location IDs (e.g., ["2840"] for US)
    
    Returns:
        DataFrame with keyword metrics
    """
    
    if not seed_keywords:
        return pd.DataFrame()

    # Try Google Ads API first if requested
    if source == KWPSource.GOOGLE_ADS_API and GOOGLE_ADS_API_AVAILABLE:
        try:
            client = get_google_ads_client()
            if client:
                st.info("🔄 Fetching keyword data from Google Ads API...")
                df = client.fetch_keyword_ideas(
                    seed_keywords=seed_keywords, 
                    location_ids=location_ids
                )
                
                if not df.empty:
                    st.success(f"✅ Retrieved {len(df)} keywords from Google Ads API")
                    return df
                else:
                    st.warning("⚠️ Google Ads API returned no results. Using mock data...")
        except Exception as e:
            error_msg = str(e)
            if "refresh token" in error_msg.lower() or "expired" in error_msg.lower():
                st.error("🔑 Google Ads API credentials expired. Using mock data instead.")
                st.info("💡 To use real API data, update your refresh token in config/config.yaml")
            else:
                st.warning(f"⚠️ Google Ads API error: {error_msg}. Using mock data...")
    
    # Fallback to mock data
    st.info("📚 Generating educational mock data...")
    return _generate_enhanced_mock_keyword_data(seed_keywords)

def get_keyword_metrics_batch(keywords: List[str], source: KWPSource, 
                              location_ids: Optional[List[str]] = None) -> Dict[str, KeywordMetrics]:
    """
    Get keyword metrics for a batch of keywords.
    
    Args:
        keywords: List of keyword strings
        source: Data source (API or Mock)
        location_ids: Geographic targeting
    
    Returns:
        Dictionary mapping keyword -> KeywordMetrics
    """
    
    df = fetch_keyword_data(keywords, source, location_ids)
    
    if df.empty:
        st.warning("⚠️ No keyword data available")
        return {}
    
    metrics = {}
    for _, row in df.iterrows():
        kw = row['keyword']
        
        # Ensure we have valid numeric values
        avg_searches = int(row.get('avg_monthly_searches', 0))
        if avg_searches < 10:
            avg_searches = 100  # Minimum realistic value
        
        competition = str(row.get('competition', 'MEDIUM'))
        cpc_low = float(row.get('cpc_low', 0.5))
        cpc_high = float(row.get('cpc_high', 2.0))
        
        # Ensure CPC values are realistic
        if cpc_low <= 0:
            cpc_low = 0.25
        if cpc_high <= cpc_low:
            cpc_high = cpc_low * 2.5
        
        metrics[kw] = KeywordMetrics(
            keyword=kw,
            avg_monthly_searches=avg_searches,
            competition=competition,
            cpc_low=cpc_low,
            cpc_high=cpc_high
        )
    
    return metrics

def _generate_enhanced_mock_keyword_data(seed_keywords: List[str]) -> pd.DataFrame:
    """
    Generate deterministic, realistic mock keyword data for educational purposes.
    
    This uses logical formulas based on:
    - Keyword length (longer = more specific = lower volume)
    - Commercial intent terms (buy, price, etc.)
    - Industry patterns
    
    Returns consistent data for the same seed keywords.
    """
    
    mock_data = []
    
    # Commercial intent scoring
    commercial_terms = {
        'buy', 'purchase', 'price', 'cheap', 'best', 'review',
        'deal', 'discount', 'sale', 'shop', 'order', 'online',
        'compare', 'vs', 'versus', 'cost', 'affordable'
    }
    
    for seed_idx, seed in enumerate(seed_keywords):
        seed_lower = seed.lower()
        
        # ========== DETERMINE COMMERCIAL INTENT ==========
        intent_score = sum(1 for term in commercial_terms if term in seed_lower)
        intent_level = min(3, intent_score)  # 0-3 scale
        
        # ========== CALCULATE BASE METRICS ==========
        word_count = len(seed.split())
        
        # Base search volume (deterministic based on seed index)
        base_volume = 1500 + (seed_idx * 400)
        
        # Intent increases search volume (people search more for commercial terms)
        volume_multiplier = 1.0 + (intent_level * 0.4)
        
        # Length penalty (longer keywords = more specific = fewer searches)
        length_penalty = 1.0 / (1.0 + (word_count - 1) * 0.25)
        
        # Calculate final search volume
        searches = int(base_volume * volume_multiplier * length_penalty)
        searches = max(100, min(50000, searches))
        
        # ========== DETERMINE COMPETITION ==========
        # High volume + high intent = high competition
        if searches > 10000 and intent_level >= 2:
            competition = "HIGH"
        elif searches > 3000 or intent_level >= 1:
            competition = "MEDIUM"
        else:
            competition = "LOW"
        
        # ========== CALCULATE CPC ==========
        # CPC matrix based on competition and intent
        base_cpc_matrix = {
            ("HIGH", 3): 3.20,
            ("HIGH", 2): 2.50,
            ("HIGH", 1): 1.90,
            ("HIGH", 0): 1.40,
            ("MEDIUM", 3): 1.80,
            ("MEDIUM", 2): 1.35,
            ("MEDIUM", 1): 1.00,
            ("MEDIUM", 0): 0.75,
            ("LOW", 3): 0.90,
            ("LOW", 2): 0.65,
            ("LOW", 1): 0.45,
            ("LOW", 0): 0.30
        }
        
        base_cpc = base_cpc_matrix.get((competition, intent_level), 1.0)
        
        # Add deterministic variation based on keyword characteristics
        keyword_hash = sum(ord(c) for c in seed) % 100
        variation_factor = 0.85 + (keyword_hash / 100 * 0.3)  # 0.85 to 1.15
        
        cpc_low = round(base_cpc * variation_factor * 0.75, 2)
        cpc_high = round(base_cpc * variation_factor * 1.60, 2)
        
        # ========== ADD MAIN KEYWORD ==========
        mock_data.append({
            "keyword": seed,
            "avg_monthly_searches": searches,
            "competition": competition,
            "cpc_low": max(0.10, cpc_low),
            "cpc_high": max(0.20, cpc_high),
            "forecast_impressions": int(searches * 0.20),
            "forecast_clicks": int(searches * 0.020),
            "forecast_cost": round(searches * 0.020 * base_cpc, 2)
        })
        
        # ========== GENERATE KEYWORD VARIATIONS ==========
        # Number of variations based on seed index (3-5 variations)
        num_variations = 3 + (seed_idx % 3)
        
        variation_patterns = [
            "{} online",
            "buy {}",
            "best {}",
            "{} reviews",
            "{} near me",
            "cheap {}",
            "{} for sale",
            "affordable {}",
            "{} discount",
            "compare {}"
        ]
        
        for var_idx in range(min(num_variations, len(variation_patterns))):
            pattern = variation_patterns[var_idx]
            variation = pattern.format(seed)
            
            # Variations have related but different metrics
            var_volume = int(searches * (0.25 + (var_idx * 0.10)))
            var_volume = max(50, min(var_volume, searches * 0.8))
            
            # Variations might have different competition
            if var_volume < searches * 0.3:
                var_competition = "LOW" if competition != "LOW" else competition
            else:
                var_competition = competition
            
            # Slight CPC variation
            var_multiplier = 0.85 + (var_idx * 0.08)
            var_cpc_low = round(cpc_low * var_multiplier, 2)
            var_cpc_high = round(cpc_high * var_multiplier, 2)
            
            mock_data.append({
                "keyword": variation,
                "avg_monthly_searches": var_volume,
                "competition": var_competition,
                "cpc_low": max(0.10, var_cpc_low),
                "cpc_high": max(0.20, var_cpc_high),
                "forecast_impressions": int(var_volume * 0.18),
                "forecast_clicks": int(var_volume * 0.018),
                "forecast_cost": round(var_volume * 0.018 * ((var_cpc_low + var_cpc_high) / 2), 2)
            })
    
    df = pd.DataFrame(mock_data)
    st.success(f"✅ Generated {len(df)} mock keywords with realistic patterns")
    return df
