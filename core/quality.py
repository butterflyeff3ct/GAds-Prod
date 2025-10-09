# /core/quality.py
from typing import List, Dict
import math

class QualityEngine:
    """
    Enhanced Quality Score engine that models Google's three main factors:
    1. Expected CTR
    2. Ad Relevance
    3. Landing Page Experience
    """
    
    def __init__(self):
        # Quality Score weights (Google's approximate distribution)
        self.weights = {
            'expected_ctr': 0.40,
            'ad_relevance': 0.35,
            'landing_page': 0.25
        }
        
        # Extension impact on quality
        self.extension_weights = {
            'sitelink': 0.15,
            'callout': 0.10,
            'structured_snippet': 0.08,
            'call': 0.12,
            'location': 0.10,
            'price': 0.08,
            'app': 0.07,
            'promotion': 0.10
        }

    def compute_qs(self, expected_ctr: float, ad_relevance: float, 
                   landing_page_exp: float) -> float:
        """
        Calculate Quality Score (1-10) based on three factors.
        Uses non-linear scaling to match Google's distribution.
        """
        
        # Normalize inputs (0-1 range)
        ctr_normalized = min(1.0, expected_ctr / 0.15)  # 15% CTR = perfect
        relevance_normalized = max(0.0, min(1.0, ad_relevance))
        lp_normalized = max(0.0, min(1.0, landing_page_exp))
        
        # Weighted combination
        raw_score = (
            self.weights['expected_ctr'] * ctr_normalized +
            self.weights['ad_relevance'] * relevance_normalized +
            self.weights['landing_page'] * lp_normalized
        )
        
        # Non-linear transformation (sigmoid-like curve)
        # This creates realistic distribution where most scores are 5-7
        transformed = 1 / (1 + math.exp(-6 * (raw_score - 0.5)))
        
        # Scale to 1-10
        quality_score = 1 + (transformed * 9)
        
        return max(1.0, min(10.0, round(quality_score, 1)))

    def calculate_expected_ctr(self, keyword: str, ad_headlines: List[str], 
                              historical_ctr: float = 0.05) -> float:
        """
        Calculate expected CTR based on keyword-ad alignment.
        """
        
        keyword_lower = keyword.lower()
        keyword_words = set(keyword_lower.split())
        
        # Check headline relevance
        headline_scores = []
        for headline in ad_headlines[:3]:  # Google shows top 3
            headline_lower = headline.lower()
            headline_words = set(headline_lower.split())
            
            # Exact keyword in headline = high score
            if keyword_lower in headline_lower:
                headline_scores.append(1.0)
            # All keyword words present = good score
            elif keyword_words.issubset(headline_words):
                headline_scores.append(0.8)
            # Partial match = medium score
            elif len(keyword_words.intersection(headline_words)) > 0:
                overlap_ratio = len(keyword_words.intersection(headline_words)) / len(keyword_words)
                headline_scores.append(0.4 + (overlap_ratio * 0.4))
            else:
                headline_scores.append(0.2)
        
        # Average of top headlines
        avg_headline_relevance = sum(headline_scores) / len(headline_scores) if headline_scores else 0.3
        
        # Combine with historical performance
        base_ctr = max(0.01, historical_ctr)
        relevance_multiplier = 0.5 + (avg_headline_relevance * 1.5)
        
        expected_ctr = base_ctr * relevance_multiplier
        
        return min(0.20, expected_ctr)  # Cap at 20%

    def calculate_ad_relevance(self, keyword: str, ad_text: str, query: str) -> float:
        """
        Calculate ad relevance score (0-1) based on keyword-ad-query alignment.
        """
        
        keyword_words = set(keyword.lower().split())
        ad_words = set(ad_text.lower().split())
        query_words = set(query.lower().split())
        
        # Keyword-Query relevance
        kw_query_overlap = len(keyword_words.intersection(query_words))
        kw_query_score = kw_query_overlap / len(query_words) if query_words else 0
        
        # Ad-Query relevance  
        ad_query_overlap = len(ad_words.intersection(query_words))
        ad_query_score = ad_query_overlap / len(query_words) if query_words else 0
        
        # Keyword-Ad relevance
        kw_ad_overlap = len(keyword_words.intersection(ad_words))
        kw_ad_score = kw_ad_overlap / len(keyword_words) if keyword_words else 0
        
        # Combined relevance score
        relevance = (
            kw_query_score * 0.4 +  # Keyword matches query
            ad_query_score * 0.4 +  # Ad matches query
            kw_ad_score * 0.2       # Keyword in ad
        )
        
        # Boost for exact matches
        if keyword.lower() in ad_text.lower():
            relevance = min(1.0, relevance * 1.2)
        
        return max(0.1, min(1.0, relevance))

    def calculate_landing_page_experience(self, url: str, keyword: str,
                                         has_mobile_friendly: bool = True,
                                         load_time_seconds: float = 2.0) -> float:
        """
        Estimate landing page experience score based on URL quality signals.
        """
        
        if not url or url == "":
            return 0.5  # Below average for missing URL
        
        score = 0.5  # Start at average
        
        # URL structure quality
        url_lower = url.lower()
        
        # HTTPS = small boost
        if url_lower.startswith('https://'):
            score += 0.05
        
        # Keyword in URL = relevance boost
        keyword_words = keyword.lower().split()
        for word in keyword_words:
            if len(word) > 3 and word in url_lower:
                score += 0.08
        
        # URL complexity (simpler = better)
        url_complexity = min(1.0, len(url) / 80.0)
        score += 0.1 * (1 - url_complexity)
        
        # Mobile friendliness
        if has_mobile_friendly:
            score += 0.15
        
        # Load time impact (under 3 seconds = good)
        if load_time_seconds <= 2.0:
            score += 0.15
        elif load_time_seconds <= 3.0:
            score += 0.10
        elif load_time_seconds <= 4.0:
            score += 0.05
        
        # Professional domain indicators
        if any(tld in url_lower for tld in ['.com', '.org', '.edu', '.gov']):
            score += 0.05
        
        return max(0.1, min(1.0, score))

    def compute_asset_uplift(self, extensions: List[Dict], alpha: float = 1.0) -> float:
        """
        Calculate CTR uplift from ad extensions.
        """
        
        if not extensions:
            return 1.0  # No uplift without extensions
        
        total_uplift = 0.0
        
        for ext in extensions:
            ext_type = ext.get('type', 'unknown')
            weight = self.extension_weights.get(ext_type, 0.05)
            
            # Quality of extension matters
            ext_quality = ext.get('quality', 0.8)  # Default good quality
            total_uplift += weight * ext_quality
        
        # Apply alpha parameter for scaling
        final_uplift = 1.0 + (total_uplift * alpha)
        
        return min(2.0, final_uplift)  # Cap at 2x uplift

    def get_quality_breakdown(self, expected_ctr: float, ad_relevance: float,
                             landing_page_exp: float) -> Dict[str, any]:
        """
        Return detailed Quality Score breakdown for educational purposes.
        """
        
        qs = self.compute_qs(expected_ctr, ad_relevance, landing_page_exp)
        
        # Component ratings (Above Average / Average / Below Average)
        def rate_component(value: float) -> str:
            if value >= 0.7:
                return "Above Average"
            elif value >= 0.4:
                return "Average"
            else:
                return "Below Average"
        
        return {
            'quality_score': qs,
            'expected_ctr': {
                'value': expected_ctr,
                'rating': rate_component(expected_ctr / 0.15)
            },
            'ad_relevance': {
                'value': ad_relevance,
                'rating': rate_component(ad_relevance)
            },
            'landing_page_experience': {
                'value': landing_page_exp,
                'rating': rate_component(landing_page_exp)
            }
        }
