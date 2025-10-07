# /core/rsa_engine.py
"""
Responsive Search Ads (RSA) Engine
Handles RSA learning, optimization, and ad rotation logic
"""

import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

@dataclass
class RSAHeadline:
    text: str
    performance_score: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    status: str = "enabled"  # enabled, paused, removed

@dataclass
class RSADescription:
    text: str
    performance_score: float = 0.0
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    status: str = "enabled"

@dataclass
class RSAAd:
    headlines: List[RSAHeadline]
    descriptions: List[RSADescription]
    ad_group_id: str
    ad_id: str
    learning_status: str = "learning"  # learning, optimized, limited
    ad_strength: str = "unknown"  # unknown, poor, average, good, excellent
    rotation_type: str = "optimize"  # optimize, rotate_evenly

class RSAEngine:
    """Handles Responsive Search Ads learning and optimization"""
    
    def __init__(self):
        self.learning_threshold = 1000  # Impressions needed for learning phase
        self.optimization_threshold = 5000  # Impressions needed for optimization
        
    def calculate_ad_strength(self, ad: RSAAd) -> str:
        """Calculate Ad Strength for RSA"""
        score = 0
        
        # Headline count (0-25 points)
        headline_count = len([h for h in ad.headlines if h.status == "enabled"])
        if headline_count >= 15:
            score += 25
        elif headline_count >= 10:
            score += 20
        elif headline_count >= 5:
            score += 15
        elif headline_count >= 3:
            score += 10
        
        # Description count (0-15 points)
        desc_count = len([d for d in ad.descriptions if d.status == "enabled"])
        if desc_count >= 4:
            score += 15
        elif desc_count >= 3:
            score += 12
        elif desc_count >= 2:
            score += 8
        
        # Length optimization (0-20 points)
        if headline_count > 0:
            avg_headline_length = sum(len(h.text) for h in ad.headlines if h.status == "enabled") / headline_count
            if 20 <= avg_headline_length <= 30:
                score += 10
            elif 15 <= avg_headline_length <= 35:
                score += 5
        
        if desc_count > 0:
            avg_desc_length = sum(len(d.text) for d in ad.descriptions if d.status == "enabled") / desc_count
            if 70 <= avg_desc_length <= 90:
                score += 10
            elif 60 <= avg_desc_length <= 95:
                score += 5
        
        # Diversity bonus (0-10 points)
        unique_words_headlines = set()
        for headline in ad.headlines:
            if headline.status == "enabled":
                unique_words_headlines.update(headline.text.lower().split())
        
        if len(unique_words_headlines) > 50:
            score += 10
        elif len(unique_words_headlines) > 30:
            score += 5
        
        # Convert score to rating
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "average"
        else:
            return "poor"
    
    def generate_rsa_combination(self, ad: RSAAd, rotation_type: str = "optimize") -> Tuple[str, str]:
        """Generate a headline/description combination for RSA"""
        
        enabled_headlines = [h for h in ad.headlines if h.status == "enabled"]
        enabled_descriptions = [d for d in ad.descriptions if d.status == "enabled"]
        
        if not enabled_headlines or not enabled_descriptions:
            return "No headlines available", "No descriptions available"
        
        if rotation_type == "rotate_evenly":
            # Even rotation - random selection
            headline = random.choice(enabled_headlines)
            description = random.choice(enabled_descriptions)
        else:
            # Optimize rotation - performance-based selection
            headline = self._select_optimized_headline(enabled_headlines)
            description = self._select_optimized_description(enabled_descriptions)
        
        return headline.text, description.text
    
    def _select_optimized_headline(self, headlines: List[RSAHeadline]) -> RSAHeadline:
        """Select headline based on performance optimization"""
        if not headlines:
            return headlines[0]
        
        # Calculate selection probabilities based on performance
        total_score = sum(h.performance_score for h in headlines if h.performance_score > 0)
        
        if total_score == 0:
            # No performance data - use even distribution with slight random variation
            weights = [1.0 + random.uniform(-0.2, 0.2) for _ in headlines]
        else:
            # Performance-based selection with some exploration
            weights = []
            for h in headlines:
                if h.performance_score > 0:
                    # Performance score + small exploration factor
                    weight = h.performance_score + random.uniform(0, 0.1)
                else:
                    # New headlines get exploration weight
                    weight = 0.1 + random.uniform(0, 0.05)
                weights.append(weight)
        
        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(headlines)
        
        rand_val = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand_val <= cumulative:
                return headlines[i]
        
        return headlines[-1]  # Fallback
    
    def _select_optimized_description(self, descriptions: List[RSADescription]) -> RSADescription:
        """Select description based on performance optimization"""
        if not descriptions:
            return descriptions[0]
        
        # Similar logic to headlines
        total_score = sum(d.performance_score for d in descriptions if d.performance_score > 0)
        
        if total_score == 0:
            weights = [1.0 + random.uniform(-0.2, 0.2) for _ in descriptions]
        else:
            weights = []
            for d in descriptions:
                if d.performance_score > 0:
                    weight = d.performance_score + random.uniform(0, 0.1)
                else:
                    weight = 0.1 + random.uniform(0, 0.05)
                weights.append(weight)
        
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(descriptions)
        
        rand_val = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand_val <= cumulative:
                return descriptions[i]
        
        return descriptions[-1]
    
    def update_performance(self, ad: RSAAd, headline_text: str, description_text: str, 
                          clicks: int, impressions: int, conversions: int = 0):
        """Update performance data for RSA components"""
        
        # Update headline performance
        for headline in ad.headlines:
            if headline.text == headline_text:
                headline.impressions += impressions
                headline.clicks += clicks
                headline.conversions += conversions
                
                # Calculate performance score (CTR * CVR * 100)
                if headline.impressions > 0:
                    ctr = headline.clicks / headline.impressions
                    cvr = headline.conversions / max(headline.clicks, 1)
                    headline.performance_score = ctr * cvr * 100
                break
        
        # Update description performance
        for description in ad.descriptions:
            if description.text == description_text:
                description.impressions += impressions
                description.clicks += clicks
                description.conversions += conversions
                
                # Calculate performance score
                if description.impressions > 0:
                    ctr = description.clicks / description.impressions
                    cvr = description.conversions / max(description.clicks, 1)
                    description.performance_score = ctr * cvr * 100
                break
    
    def get_learning_status(self, ad: RSAAd) -> str:
        """Determine RSA learning status"""
        total_impressions = sum(h.impressions for h in ad.headlines)
        
        if total_impressions < self.learning_threshold:
            return "learning"
        elif total_impressions < self.optimization_threshold:
            return "limited"
        else:
            return "optimized"
    
    def get_performance_insights(self, ad: RSAAd) -> Dict:
        """Get RSA performance insights"""
        enabled_headlines = [h for h in ad.headlines if h.status == "enabled"]
        enabled_descriptions = [d for d in ad.descriptions if d.status == "enabled"]
        
        # Headline insights
        headline_performance = []
        for h in enabled_headlines:
            if h.impressions > 0:
                headline_performance.append({
                    "text": h.text,
                    "ctr": h.clicks / h.impressions,
                    "cvr": h.conversions / max(h.clicks, 1),
                    "performance_score": h.performance_score,
                    "impressions": h.impressions
                })
        
        # Description insights
        description_performance = []
        for d in enabled_descriptions:
            if d.impressions > 0:
                description_performance.append({
                    "text": d.text,
                    "ctr": d.clicks / d.impressions,
                    "cvr": d.conversions / max(d.clicks, 1),
                    "performance_score": d.performance_score,
                    "impressions": d.impressions
                })
        
        return {
            "learning_status": self.get_learning_status(ad),
            "ad_strength": self.calculate_ad_strength(ad),
            "headline_performance": sorted(headline_performance, key=lambda x: x["performance_score"], reverse=True),
            "description_performance": sorted(description_performance, key=lambda x: x["performance_score"], reverse=True),
            "total_impressions": sum(h.impressions for h in ad.headlines),
            "recommendations": self._generate_recommendations(ad)
        }
    
    def _generate_recommendations(self, ad: RSAAd) -> List[str]:
        """Generate recommendations for RSA improvement"""
        recommendations = []
        
        enabled_headlines = [h for h in ad.headlines if h.status == "enabled"]
        enabled_descriptions = [d for d in ad.descriptions if d.status == "enabled"]
        
        # Headline recommendations
        if len(enabled_headlines) < 15:
            recommendations.append(f"Add {15 - len(enabled_headlines)} more headlines to reach the recommended 15 headlines")
        
        if len(enabled_descriptions) < 4:
            recommendations.append(f"Add {4 - len(enabled_descriptions)} more descriptions to reach the recommended 4 descriptions")
        
        # Performance-based recommendations
        low_performing_headlines = [h for h in enabled_headlines if h.impressions > 100 and h.performance_score < 1.0]
        if low_performing_headlines:
            recommendations.append(f"Consider pausing or improving {len(low_performing_headlines)} low-performing headlines")
        
        low_performing_descriptions = [d for d in enabled_descriptions if d.impressions > 100 and d.performance_score < 1.0]
        if low_performing_descriptions:
            recommendations.append(f"Consider pausing or improving {len(low_performing_descriptions)} low-performing descriptions")
        
        return recommendations

# Global RSA engine instance
rsa_engine = RSAEngine()
