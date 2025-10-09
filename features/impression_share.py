# /features/impression_share.py
"""
Impression Share Calculations
Models how often your ads show vs total available impressions.
Critical metric for understanding market coverage.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ImpressionShareMetrics:
    """Complete impression share breakdown."""
    search_impression_share: float  # % of impressions you received
    search_exact_match_is: float  # IS for exact match queries
    search_top_impression_share: float  # IS in top positions
    search_absolute_top_is: float  # IS in position 1
    search_lost_is_rank: float  # IS lost due to low Ad Rank
    search_lost_is_budget: float  # IS lost due to budget constraints
    total_eligible_impressions: int  # Estimated total market impressions

class ImpressionShareCalculator:
    """
    Calculate impression share metrics.
    
    Impression Share = Your Impressions / Total Eligible Impressions
    
    You can lose impression share due to:
    1. Budget (ran out of money)
    2. Rank (Ad Rank too low to show)
    """
    
    def __init__(self, market_size_multiplier: float = 5.0):
        """
        Initialize calculator.
        
        Args:
            market_size_multiplier: How much bigger the total market is vs your impressions
                                   5.0 means total market is 5x your impression count
        """
        self.market_size_multiplier = market_size_multiplier
    
    def calculate_impression_share(self, 
                                   your_impressions: int,
                                   your_budget: float,
                                   total_spend: float,
                                   avg_position: float,
                                   avg_quality_score: float,
                                   competitor_count: int = 10) -> ImpressionShareMetrics:
        """
        Calculate comprehensive impression share metrics.
        
        Args:
            your_impressions: Total impressions you received
            your_budget: Daily budget
            total_spend: How much you actually spent
            avg_position: Average ad position
            avg_quality_score: Average Quality Score
            competitor_count: Number of competitors
        
        Returns:
            Complete impression share breakdown
        """
        
        # Estimate total eligible impressions
        # More competitors = more total market impressions
        competitor_factor = 1.0 + (competitor_count * 0.1)
        total_eligible = int(your_impressions * self.market_size_multiplier * competitor_factor)
        
        # Calculate base impression share
        search_is = (your_impressions / total_eligible) if total_eligible > 0 else 0
        
        # Estimate impressions lost to budget
        budget_exhausted = total_spend >= your_budget * 0.95
        if budget_exhausted:
            # You ran out of budget - estimate how many more impressions you could have had
            # Assume you could have gotten 30-50% more impressions with unlimited budget
            budget_loss_factor = 0.30 + (total_spend / your_budget - 0.95) * 0.20
            lost_is_budget = search_is * budget_loss_factor
        else:
            # Had budget left - minimal budget loss
            budget_utilization = total_spend / your_budget
            lost_is_budget = search_is * (1.0 - budget_utilization) * 0.1
        
        # Estimate impressions lost to rank
        # Lower positions and lower QS = more rank loss
        position_factor = avg_position / 4.0  # Normalize to 0-1 (assuming 4 positions)
        qs_factor = (10 - avg_quality_score) / 9.0  # Lower QS = higher loss
        
        rank_loss_potential = (position_factor * 0.5) + (qs_factor * 0.5)
        lost_is_rank = search_is * rank_loss_potential * 0.3
        
        # Calculate top of page IS (positions 1-4)
        # Assume you got top positions for most of your impressions
        top_is = search_is * (1.0 - (avg_position - 1) * 0.2)
        top_is = max(0, min(search_is, top_is))
        
        # Calculate absolute top IS (position 1 only)
        # Estimate based on how often you were in position 1
        position_1_rate = max(0, 1.0 - (avg_position - 1) * 0.4)
        absolute_top_is = search_is * position_1_rate
        
        # Exact match IS (assume slightly better than overall)
        exact_match_is = min(1.0, search_is * 1.1)
        
        return ImpressionShareMetrics(
            search_impression_share=round(search_is * 100, 2),
            search_exact_match_is=round(exact_match_is * 100, 2),
            search_top_impression_share=round(top_is * 100, 2),
            search_absolute_top_is=round(absolute_top_is * 100, 2),
            search_lost_is_rank=round(lost_is_rank * 100, 2),
            search_lost_is_budget=round(lost_is_budget * 100, 2),
            total_eligible_impressions=total_eligible
        )
    
    def get_is_recommendations(self, metrics: ImpressionShareMetrics) -> List[str]:
        """
        Get recommendations for improving impression share.
        Educational function.
        """
        recommendations = []
        
        # Overall IS check
        if metrics.search_impression_share < 20:
            recommendations.append('⚠️ Very low impression share (<20%)')
            recommendations.append('You\'re missing most of the available traffic.')
        elif metrics.search_impression_share < 50:
            recommendations.append('📊 Moderate impression share (20-50%)')
            recommendations.append('Good starting point, but room to grow.')
        else:
            recommendations.append('✅ Strong impression share (50%+)')
            recommendations.append('You\'re capturing a significant portion of the market.')
        
        # Budget loss
        if metrics.search_lost_is_budget > 20:
            recommendations.append('\n💰 High budget loss (>20%):')
            recommendations.append('  • Increase daily budget')
            recommendations.append('  • Use automated bidding to optimize spend')
            recommendations.append('  • Focus on high-converting keywords')
            recommendations.append('  • Pause low-performing keywords')
        
        # Rank loss
        if metrics.search_lost_is_rank > 20:
            recommendations.append('\n📈 High rank loss (>20%):')
            recommendations.append('  • Improve Quality Score')
            recommendations.append('  • Increase bids')
            recommendations.append('  • Add ad extensions')
            recommendations.append('  • Improve ad relevance')
        
        # Top position analysis
        if metrics.search_absolute_top_is < 10:
            recommendations.append('\n🎯 Low absolute top impression share:')
            recommendations.append('  • Rarely appearing in position 1')
            recommendations.append('  • Increase bids for top positions')
            recommendations.append('  • Focus on high-QS keywords')
        
        # Actionable summary
        if metrics.search_lost_is_budget > metrics.search_lost_is_rank:
            recommendations.append('\n💡 Primary issue: Budget constraints')
            recommendations.append('→ Focus on increasing budget or improving efficiency')
        else:
            recommendations.append('\n💡 Primary issue: Ad Rank')
            recommendations.append('→ Focus on improving bids and Quality Score')
        
        return recommendations
    
    def compare_to_benchmarks(self, metrics: ImpressionShareMetrics, 
                             industry: str = "general") -> Dict:
        """
        Compare your IS to industry benchmarks.
        
        Industry benchmarks (approximate):
        - Retail: 40-60% IS typical
        - B2B: 30-50% IS typical
        - Finance: 20-40% IS (very competitive)
        - Local: 50-70% IS typical
        """
        benchmarks = {
            "general": {"good": 50, "average": 30, "poor": 15},
            "retail": {"good": 60, "average": 40, "poor": 20},
            "b2b": {"good": 50, "average": 30, "poor": 15},
            "finance": {"good": 40, "average": 25, "poor": 10},
            "local": {"good": 70, "average": 50, "poor": 30}
        }
        
        benchmark = benchmarks.get(industry, benchmarks["general"])
        your_is = metrics.search_impression_share
        
        if your_is >= benchmark["good"]:
            performance = "excellent"
            message = f"Your IS is above the {industry} industry benchmark!"
        elif your_is >= benchmark["average"]:
            performance = "good"
            message = f"Your IS is around the {industry} industry average."
        elif your_is >= benchmark["poor"]:
            performance = "below_average"
            message = f"Your IS is below the {industry} industry average."
        else:
            performance = "poor"
            message = f"Your IS is significantly below the {industry} industry benchmark."
        
        return {
            'performance': performance,
            'message': message,
            'your_is': your_is,
            'industry_good': benchmark["good"],
            'industry_average': benchmark["average"],
            'gap_to_good': benchmark["good"] - your_is
        }
