# /core/pacing.py
from typing import List, Dict, Optional

class PacingController:
    """
    Enhanced budget pacing controller with realistic hourly distribution curves.
    Models how Google Ads distributes budget throughout the day.
    """
    
    def __init__(self, daily_budget: float, beta: float = 0.8, 
                 pacing_strategy: str = "standard", hourly_curve: Optional[List[float]] = None):
        """
        Initialize pacing controller.
        
        Args:
            daily_budget: Total daily budget
            beta: Aggressiveness factor (0.5-1.0, higher = faster spend)
            pacing_strategy: "standard", "accelerated", or "custom"
            hourly_curve: Custom hourly distribution (must sum to 1.0)
        """
        self.daily_budget = daily_budget
        self.beta = beta
        self.pacing_strategy = pacing_strategy
        
        # Set hourly curve based on strategy
        if hourly_curve:
            total = sum(hourly_curve)
            self.hourly_curve = [h / total for h in hourly_curve]
        else:
            self.hourly_curve = self._get_pacing_curve(pacing_strategy)
        
        self.total_spend = 0.0
        self.current_hour = 0
        self.throttle_factor = 1.0
        self.hourly_budgets = [self.daily_budget * h for h in self.hourly_curve]
        self.hourly_spend = [0.0] * 24
        
    def _get_pacing_curve(self, strategy: str) -> List[float]:
        """
        Get hourly distribution curve based on pacing strategy.
        
        Standard: Matches typical search volume (higher during business hours)
        Accelerated: Aggressive early spend
        Even: Uniform distribution
        """
        if strategy == "standard":
            # Realistic hourly distribution matching typical search patterns
            # Higher during business hours (9am-5pm), lower at night
            return [
                0.02, 0.01, 0.01, 0.01, 0.02, 0.03,  # 12am-5am (2%)
                0.04, 0.05, 0.06, 0.07, 0.08, 0.08,  # 6am-11am (38%)
                0.07, 0.07, 0.06, 0.06, 0.07, 0.08,  # 12pm-5pm (41%)
                0.07, 0.06, 0.05, 0.04, 0.03, 0.02   # 6pm-11pm (27%)
            ]
        elif strategy == "accelerated":
            # Front-loaded spending (spend budget as fast as possible)
            # High early, drops off quickly
            return [
                0.10, 0.09, 0.08, 0.08, 0.07, 0.07,  # Early morning burst
                0.06, 0.06, 0.05, 0.05, 0.04, 0.04,  # Declining
                0.03, 0.03, 0.03, 0.02, 0.02, 0.02,  # Lower afternoon
                0.02, 0.02, 0.01, 0.01, 0.01, 0.01   # Minimal evening
            ]
        else:  # "even"
            # Uniform distribution
            return [1/24] * 24

    def update_hour(self, hour: int):
        """Update to new hour and recalculate throttle."""
        self.current_hour = hour
        self._recalculate_throttle()

    def record_spend(self, amount: float):
        """Record spend for current hour."""
        self.total_spend += amount
        self.hourly_spend[self.current_hour] += amount

    def apply_throttle(self, bid: float) -> float:
        """Apply throttle factor to bid."""
        return bid * self.throttle_factor

    def reset_daily(self):
        """Reset controller for a new day."""
        self.total_spend = 0.0
        self.current_hour = 0
        self.throttle_factor = 1.0
        self.hourly_spend = [0.0] * 24
        self.hourly_budgets = [self.daily_budget * h for h in self.hourly_curve]

    def should_participate(self) -> bool:
        """
        Check if controller should participate in auctions.
        More sophisticated than just budget check.
        """
        # Budget exhausted
        if self.total_spend >= self.daily_budget:
            return False
        
        # Throttle is too low (effectively paused)
        if self.throttle_factor < 0.1:
            return False
        
        # Check if we have budget left for this hour
        hours_elapsed = self.current_hour + 1
        expected_spend = sum(self.hourly_budgets[:hours_elapsed])
        remaining_budget = self.daily_budget - self.total_spend
        
        # If we're way over budget for this hour, pause
        if self.total_spend > expected_spend * 1.5:
            return False
        
        return True

    def get_pacing_status(self) -> Dict:
        """Get detailed pacing status for analysis."""
        hours_elapsed = self.current_hour + 1
        expected_spend = sum(self.hourly_budgets[:hours_elapsed])
        spend_rate = self.total_spend / expected_spend if expected_spend > 0 else 1.0
        
        return {
            'total_spend': round(self.total_spend, 2),
            'daily_budget': self.daily_budget,
            'current_hour': self.current_hour,
            'throttle_factor': round(self.throttle_factor, 3),
            'expected_spend': round(expected_spend, 2),
            'spend_rate': round(spend_rate, 3),
            'budget_remaining': round(self.daily_budget - self.total_spend, 2),
            'budget_utilization': round((self.total_spend / self.daily_budget) * 100, 1),
            'should_participate': self.should_participate(),
            'hourly_spend': self.hourly_spend[:hours_elapsed],
            'hourly_target': self.hourly_budgets[:hours_elapsed],
            'pacing_strategy': self.pacing_strategy
        }

    def _recalculate_throttle(self):
        """
        Recalculate throttle factor based on spend rate.
        
        This is the sophisticated logic that Google Ads uses to pace spend:
        - If spending too fast → reduce bids (throttle down)
        - If spending too slow → increase bids (throttle up)
        - Considers time of day and remaining budget
        """
        hours_elapsed = self.current_hour + 1
        expected_spend = sum(self.hourly_budgets[:hours_elapsed])
        
        # Budget exhausted - stop bidding
        if self.total_spend >= self.daily_budget:
            self.throttle_factor = 0.0
            return
        
        # Calculate spend rate
        if expected_spend > 0:
            spend_rate = self.total_spend / expected_spend
        else:
            spend_rate = 0.0
        
        # Calculate remaining budget runway
        hours_remaining = 24 - self.current_hour
        remaining_budget = self.daily_budget - self.total_spend
        
        if hours_remaining > 0:
            avg_hourly_budget_remaining = remaining_budget / hours_remaining
            expected_hourly_budget = self.daily_budget / 24
            runway_factor = avg_hourly_budget_remaining / expected_hourly_budget
        else:
            runway_factor = 0.0
        
        # Throttle logic with smooth adjustments
        if spend_rate > 1.3:
            # Severely overspending - aggressive throttle
            self.throttle_factor = max(0.2, 1.0 / (spend_rate * 1.2))
        elif spend_rate > 1.1:
            # Moderately overspending - gentle throttle
            self.throttle_factor = max(0.5, 1.0 / spend_rate)
        elif spend_rate < 0.7:
            # Underspending - boost bids
            self.throttle_factor = min(1.8, 1.0 + (1.0 - spend_rate) * 0.5)
        elif spend_rate < 0.9:
            # Slightly underspending - gentle boost
            self.throttle_factor = min(1.3, 1.0 + (1.0 - spend_rate) * 0.3)
        else:
            # On track - maintain current pace
            self.throttle_factor = 1.0
        
        # Adjust for pacing strategy
        if self.pacing_strategy == "accelerated":
            # Always bid aggressively
            self.throttle_factor = min(2.0, self.throttle_factor * 1.5)
        
        # Apply beta (aggressiveness parameter)
        self.throttle_factor *= self.beta
        
        # Final bounds check
        self.throttle_factor = max(0.0, min(3.0, self.throttle_factor))

    def get_hourly_performance(self) -> Dict:
        """
        Get hour-by-hour performance analysis.
        Educational function showing how pacing worked each hour.
        """
        performance = []
        for hour in range(24):
            if hour <= self.current_hour:
                performance.append({
                    'hour': hour,
                    'target_budget': round(self.hourly_budgets[hour], 2),
                    'actual_spend': round(self.hourly_spend[hour], 2),
                    'variance': round(self.hourly_spend[hour] - self.hourly_budgets[hour], 2),
                    'variance_pct': round(
                        ((self.hourly_spend[hour] / self.hourly_budgets[hour]) - 1) * 100, 1
                    ) if self.hourly_budgets[hour] > 0 else 0
                })
        
        return {
            'hourly_data': performance,
            'total_variance': round(self.total_spend - sum(self.hourly_budgets[:self.current_hour + 1]), 2),
            'avg_hourly_variance_pct': round(
                sum(p['variance_pct'] for p in performance) / len(performance), 1
            ) if performance else 0
        }

    def predict_end_of_day_spend(self) -> Dict:
        """
        Predict final daily spend based on current pacing.
        Useful for forecasting and alerting.
        """
        hours_elapsed = self.current_hour + 1
        hours_remaining = 24 - hours_elapsed
        
        if hours_elapsed == 0:
            return {
                'predicted_spend': 0,
                'prediction_confidence': 'low',
                'will_exhaust_budget': False,
                'estimated_hour_of_exhaustion': None
            }
        
        # Calculate current spend rate
        current_hourly_avg = self.total_spend / hours_elapsed
        
        # Project remaining hours
        if hours_remaining > 0:
            expected_remaining_spend = sum(self.hourly_budgets[hours_elapsed:]) * self.throttle_factor
            predicted_spend = self.total_spend + expected_remaining_spend
        else:
            predicted_spend = self.total_spend
        
        # Confidence based on hours elapsed
        if hours_elapsed < 6:
            confidence = 'low'
        elif hours_elapsed < 12:
            confidence = 'medium'
        else:
            confidence = 'high'
        
        # Estimate when budget will be exhausted
        will_exhaust = predicted_spend >= self.daily_budget
        if will_exhaust and current_hourly_avg > 0:
            hours_until_exhaustion = (self.daily_budget - self.total_spend) / current_hourly_avg
            estimated_hour = min(23, self.current_hour + int(hours_until_exhaustion))
        else:
            estimated_hour = None
        
        return {
            'predicted_spend': round(predicted_spend, 2),
            'prediction_confidence': confidence,
            'will_exhaust_budget': will_exhaust,
            'estimated_hour_of_exhaustion': estimated_hour,
            'budget_utilization_forecast': round((predicted_spend / self.daily_budget) * 100, 1)
        }
