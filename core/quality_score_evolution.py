# /core/quality_score_evolution.py
"""
Quality Score Evolution Module
Models how Quality Score changes over time based on actual performance.
In real Google Ads, QS improves when your CTR is consistently good.
"""

from typing import Dict, List
from dataclasses import dataclass
from collections import deque

@dataclass
class QualityScoreHistory:
    """Tracks Quality Score changes over time."""
    keyword_id: str
    current_qs: float
    history: deque  # Recent QS values
    ctr_history: deque  # Recent CTR values
    relevance_history: deque  # Recent relevance scores
    
class QualityScoreEvolutionEngine:
    """
    Models how Quality Score evolves based on performance.
    
    Key principles (based on Google Ads):
    1. Expected CTR improves when actual CTR exceeds expectations
    2. Ad relevance improves with consistent keyword-ad alignment
    3. Landing page experience improves with low bounce rates
    4. Changes happen gradually (not overnight)
    """
    
    def __init__(self, evolution_rate: float = 0.1):
        self.keyword_qs: Dict[str, QualityScoreHistory] = {}
        self.evolution_rate = evolution_rate  # How fast QS can change (0.0-1.0)
        self.min_data_points = 10  # Need this many auctions before adjusting
        
    def initialize_keyword(self, keyword_id: str, initial_qs: float):
        """Initialize tracking for a keyword."""
        self.keyword_qs[keyword_id] = QualityScoreHistory(
            keyword_id=keyword_id,
            current_qs=initial_qs,
            history=deque(maxlen=30),  # Keep last 30 QS values
            ctr_history=deque(maxlen=100),  # Keep last 100 CTR values
            relevance_history=deque(maxlen=50)
        )
        self.keyword_qs[keyword_id].history.append(initial_qs)
    
    def record_performance(self, keyword_id: str, actual_ctr: float, 
                          expected_ctr: float, ad_relevance: float):
        """
        Record performance metrics for a keyword.
        
        Args:
            keyword_id: Keyword identifier
            actual_ctr: Actual CTR achieved
            expected_ctr: What was expected
            ad_relevance: Relevance score (0-1)
        """
        if keyword_id not in self.keyword_qs:
            return  # Not tracking this keyword
        
        qs_data = self.keyword_qs[keyword_id]
        qs_data.ctr_history.append(actual_ctr)
        qs_data.relevance_history.append(ad_relevance)
    
    def update_quality_scores(self, day: int) -> Dict[str, float]:
        """
        Update all Quality Scores based on accumulated performance data.
        Should be called daily or after significant data accumulation.
        
        Returns:
            Dictionary of keyword_id -> new_quality_score
        """
        updated_scores = {}
        
        for keyword_id, qs_data in self.keyword_qs.items():
            # Need minimum data points to make changes
            if len(qs_data.ctr_history) < self.min_data_points:
                updated_scores[keyword_id] = qs_data.current_qs
                continue
            
            # Calculate performance indicators
            avg_ctr = sum(qs_data.ctr_history) / len(qs_data.ctr_history)
            avg_relevance = sum(qs_data.relevance_history) / len(qs_data.relevance_history) if qs_data.relevance_history else 0.7
            
            # Determine if performance is above or below expectations
            ctr_performance = self._evaluate_ctr_performance(avg_ctr, qs_data.current_qs)
            
            # Calculate QS adjustment
            qs_adjustment = 0.0
            
            # 1. CTR component (40% of QS weight)
            if ctr_performance > 1.2:
                # Excellent CTR - improve QS
                qs_adjustment += 0.3 * self.evolution_rate
            elif ctr_performance > 1.0:
                # Good CTR - slight improvement
                qs_adjustment += 0.1 * self.evolution_rate
            elif ctr_performance < 0.8:
                # Poor CTR - decrease QS
                qs_adjustment -= 0.2 * self.evolution_rate
            elif ctr_performance < 0.95:
                # Below average CTR - slight decrease
                qs_adjustment -= 0.1 * self.evolution_rate
            
            # 2. Ad relevance component (35% of QS weight)
            if avg_relevance > 0.8:
                qs_adjustment += 0.15 * self.evolution_rate
            elif avg_relevance < 0.5:
                qs_adjustment -= 0.15 * self.evolution_rate
            
            # 3. Consistency bonus (stable performance = gradual improvement)
            if len(qs_data.ctr_history) >= 50:
                ctr_variance = self._calculate_variance(list(qs_data.ctr_history))
                if ctr_variance < 0.01:  # Very consistent
                    qs_adjustment += 0.1 * self.evolution_rate
            
            # Apply adjustment
            new_qs = qs_data.current_qs + qs_adjustment
            
            # Bound QS to 1-10 range
            new_qs = max(1.0, min(10.0, new_qs))
            
            # Update tracking
            qs_data.current_qs = new_qs
            qs_data.history.append(new_qs)
            
            updated_scores[keyword_id] = new_qs
        
        return updated_scores
    
    def _evaluate_ctr_performance(self, actual_ctr: float, current_qs: float) -> float:
        """
        Compare actual CTR to expected CTR based on Quality Score.
        
        Returns:
            Ratio of actual/expected (1.0 = meeting expectations)
        """
        # Expected CTR increases with QS
        # QS 1-3: 1-2% expected
        # QS 4-6: 2-4% expected
        # QS 7-10: 4-8% expected
        if current_qs <= 3:
            expected_ctr = 0.01 + (current_qs - 1) * 0.005
        elif current_qs <= 6:
            expected_ctr = 0.02 + (current_qs - 4) * 0.01
        else:
            expected_ctr = 0.04 + (current_qs - 7) * 0.013
        
        if expected_ctr == 0:
            return 1.0
        
        return actual_ctr / expected_ctr
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        squared_diffs = [(x - mean) ** 2 for x in values]
        variance = sum(squared_diffs) / len(values)
        
        return variance
    
    def get_qs_trend(self, keyword_id: str) -> Dict:
        """
        Get Quality Score trend data for a keyword.
        Educational function showing how QS changed over time.
        """
        if keyword_id not in self.keyword_qs:
            return {'error': 'Keyword not found'}
        
        qs_data = self.keyword_qs[keyword_id]
        
        trend = {
            'keyword_id': keyword_id,
            'current_qs': round(qs_data.current_qs, 1),
            'initial_qs': round(list(qs_data.history)[0], 1) if qs_data.history else 0,
            'change': round(qs_data.current_qs - list(qs_data.history)[0], 1) if qs_data.history else 0,
            'history': [round(qs, 1) for qs in list(qs_data.history)],
            'data_points': len(qs_data.ctr_history)
        }
        
        # Determine trend direction
        if len(qs_data.history) >= 5:
            recent_trend = list(qs_data.history)[-5:]
            if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                trend['trend'] = 'improving'
            elif all(recent_trend[i] >= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                trend['trend'] = 'declining'
            else:
                trend['trend'] = 'stable'
        else:
            trend['trend'] = 'insufficient_data'
        
        # Performance assessment
        if len(qs_data.ctr_history) >= self.min_data_points:
            avg_ctr = sum(qs_data.ctr_history) / len(qs_data.ctr_history)
            performance_ratio = self._evaluate_ctr_performance(avg_ctr, qs_data.current_qs)
            
            if performance_ratio > 1.2:
                trend['performance'] = 'excellent'
                trend['recommendation'] = 'Keep doing what you\'re doing! Your CTR is excellent.'
            elif performance_ratio > 1.0:
                trend['performance'] = 'good'
                trend['recommendation'] = 'Good performance. Quality Score should continue improving.'
            elif performance_ratio > 0.9:
                trend['performance'] = 'average'
                trend['recommendation'] = 'Meeting expectations. Room for improvement.'
            else:
                trend['performance'] = 'below_average'
                trend['recommendation'] = 'CTR is below expectations. Consider improving ad copy or keyword targeting.'
        else:
            trend['performance'] = 'insufficient_data'
            trend['recommendation'] = f'Need {self.min_data_points - len(qs_data.ctr_history)} more data points for analysis.'
        
        return trend
    
    def get_improvement_recommendations(self, keyword_id: str) -> List[str]:
        """
        Get specific recommendations for improving Quality Score.
        Educational function.
        """
        if keyword_id not in self.keyword_qs:
            return ['Keyword not being tracked']
        
        qs_data = self.keyword_qs[keyword_id]
        recommendations = []
        
        # Check CTR performance
        if len(qs_data.ctr_history) >= 10:
            avg_ctr = sum(qs_data.ctr_history) / len(qs_data.ctr_history)
            
            if avg_ctr < 0.02:
                recommendations.append('CTR is low. Try:')
                recommendations.append('  • Include keyword in headline')
                recommendations.append('  • Add compelling call-to-action')
                recommendations.append('  • Use ad extensions')
                recommendations.append('  • Test emotional triggers')
        
        # Check relevance
        if len(qs_data.relevance_history) >= 10:
            avg_relevance = sum(qs_data.relevance_history) / len(qs_data.relevance_history)
            
            if avg_relevance < 0.6:
                recommendations.append('Ad relevance is low. Try:')
                recommendations.append('  • Match ad copy to keyword intent')
                recommendations.append('  • Create tighter ad groups')
                recommendations.append('  • Use dynamic keyword insertion')
        
        # Check Quality Score level
        if qs_data.current_qs < 5:
            recommendations.append('Quality Score needs work:')
            recommendations.append('  • Consider pausing underperforming keywords')
            recommendations.append('  • Improve landing page experience')
            recommendations.append('  • Ensure mobile-friendliness')
        
        # Consistency check
        if len(qs_data.ctr_history) >= 20:
            recent_ctrs = list(qs_data.ctr_history)[-20:]
            variance = self._calculate_variance(recent_ctrs)
            
            if variance > 0.02:
                recommendations.append('Performance is inconsistent:')
                recommendations.append('  • Review ad scheduling')
                recommendations.append('  • Check device performance')
                recommendations.append('  • Analyze by time of day')
        
        if not recommendations:
            recommendations.append('✅ Quality Score is performing well!')
            recommendations.append('Continue current strategy and monitor regularly.')
        
        return recommendations
