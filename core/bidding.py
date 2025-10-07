# /core/bidding.py
import numpy as np
import pandas as pd
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

try:
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@dataclass
class BidContext:
    hour: int = 12
    day_of_week: int = 1
    device: str = "desktop"
    quality_score: float = 5.0
    competitor_density: float = 0.5
    historical_ctr: float = 0.05
    historical_cvr: float = 0.05
    keyword_text: str = ""
    match_type: str = "broad"
    day_of_month: int = 15  # For seasonality
    is_holiday: bool = False

class SeasonalityModel:
    """
    Models seasonal patterns in search behavior.
    Different industries have different seasonal patterns.
    """
    
    def __init__(self, industry: str = "general"):
        self.industry = industry
        
        # Day of week multipliers (Mon=0, Sun=6)
        self.dow_patterns = {
            "general": [0.95, 1.00, 1.05, 1.05, 1.00, 0.85, 0.75],  # Lower weekends
            "retail": [0.90, 0.95, 1.00, 1.05, 1.10, 1.20, 1.15],   # Higher weekends
            "b2b": [1.10, 1.15, 1.10, 1.05, 1.00, 0.60, 0.55],      # Much lower weekends
            "travel": [0.85, 0.90, 0.95, 1.00, 1.05, 1.20, 1.25],   # Peak weekends
            "education": [1.05, 1.10, 1.10, 1.05, 1.00, 0.80, 0.75] # Lower weekends
        }
        
        # Month multipliers (Jan=1, Dec=12)
        self.month_patterns = {
            "general": [1.0] * 12,  # Flat
            "retail": [0.80, 0.75, 0.85, 0.90, 0.95, 0.95, 0.90, 0.95, 1.00, 1.05, 1.30, 1.50],  # Holiday peak
            "travel": [0.90, 0.85, 1.00, 1.10, 1.15, 1.30, 1.35, 1.25, 1.00, 0.95, 0.90, 0.95],  # Summer peak
            "b2b": [1.05, 1.10, 1.10, 1.05, 1.00, 0.95, 0.85, 0.90, 1.05, 1.10, 1.05, 0.85],     # Lower summer/Dec
            "education": [1.30, 1.25, 1.10, 1.00, 0.95, 0.70, 0.65, 1.20, 1.25, 1.10, 1.05, 0.85] # School cycle
        }
        
        # Major holidays (month, day) -> multiplier
        self.holidays = {
            (1, 1): 0.70,   # New Year's Day
            (2, 14): 1.20,  # Valentine's
            (7, 4): 0.80,   # Independence Day
            (11, 24): 1.40, # Black Friday (approximate)
            (12, 25): 0.50, # Christmas
            (12, 31): 0.70  # New Year's Eve
        }
    
    def get_multiplier(self, date: datetime) -> float:
        """Get combined seasonal multiplier for a date."""
        dow_pattern = self.dow_patterns.get(self.industry, self.dow_patterns["general"])
        month_pattern = self.month_patterns.get(self.industry, self.month_patterns["general"])
        
        # Day of week effect
        dow_mult = dow_pattern[date.weekday()]
        
        # Month effect
        month_mult = month_pattern[date.month - 1]
        
        # Holiday effect
        holiday_key = (date.month, date.day)
        holiday_mult = self.holidays.get(holiday_key, 1.0)
        
        # Combined (multiplicative)
        total_mult = dow_mult * month_mult * holiday_mult
        
        return total_mult

class BiddingEngine:
    """
    Enhanced bidding engine with device, time, and seasonal modifiers.
    Now includes realistic bid adjustments based on context.
    """
    
    def __init__(self, strategy: str = "manual_cpc", base_bid: float = 1.5, 
                 target_cpa: float = 20.0, target_roas: float = 4.0, 
                 use_ml: bool = False, industry: str = "general"):
        self.strategy = strategy
        self.base_bid = base_bid
        self.target_cpa = target_cpa
        self.target_roas = target_roas
        self.use_ml = use_ml and ML_AVAILABLE
        self.historical_cvr = 0.05
        self.historical_value = 100.0
        self.ctr_model = None
        self.cvr_model = None
        
        # Bid adjustments (similar to Google Ads bid adjustments)
        self.device_adjustments = {
            "desktop": 1.0,    # Baseline
            "mobile": 0.85,    # -15% (typically lower CVR)
            "tablet": 0.90     # -10%
        }
        
        # Hour of day adjustments (peak hours get boost)
        self.hour_adjustments = self._get_hourly_adjustments()
        
        # Seasonality model
        self.seasonality = SeasonalityModel(industry)
        
    def _get_hourly_adjustments(self) -> Dict[int, float]:
        """
        Generate hourly bid adjustments.
        Higher during business hours when conversion rates are typically better.
        """
        adjustments = {}
        for hour in range(24):
            if 9 <= hour <= 17:  # Business hours
                adjustments[hour] = 1.15  # +15%
            elif 6 <= hour <= 8 or 18 <= hour <= 20:  # Morning/evening
                adjustments[hour] = 1.05  # +5%
            elif 21 <= hour <= 23:  # Late evening
                adjustments[hour] = 0.95  # -5%
            else:  # Night hours (0-5)
                adjustments[hour] = 0.85  # -15%
        return adjustments
    
    def set_device_adjustment(self, device: str, adjustment: float):
        """Set custom device bid adjustment (e.g., +20% for mobile)."""
        self.device_adjustments[device] = adjustment
    
    def set_hour_adjustment(self, hour: int, adjustment: float):
        """Set custom hour bid adjustment."""
        self.hour_adjustments[hour] = adjustment

    def _context_to_features(self, context: BidContext) -> np.ndarray:
        """Convert context to feature vector for ML models."""
        return np.array([
            context.hour, 
            context.day_of_week, 
            1 if context.device == "mobile" else 0,
            context.quality_score, 
            context.competitor_density, 
            context.historical_ctr,
            1 if context.match_type == "exact" else 0,
            context.day_of_month,
            1 if context.is_holiday else 0
        ])

    def _ml_bid(self, context: BidContext) -> float:
        """ML-based bidding (requires trained models)."""
        features = self._context_to_features(context)
        pred_ctr = self.ctr_model.predict([features])[0] if self.ctr_model else context.historical_ctr
        pred_cvr = self.cvr_model.predict([features])[0] if self.cvr_model else context.historical_cvr
        
        if self.strategy == "target_cpa":
            return self.target_cpa * pred_cvr
        elif self.strategy == "target_roas":
            return (self.historical_value / self.target_roas) * pred_cvr
        return self.base_bid * (1 + pred_ctr * 5)

    def get_bid(self, cvr_hat: Optional[float] = None, value_hat: Optional[float] = None,
                context: Optional[BidContext] = None) -> float:
        """
        Calculate bid with all modifiers applied.
        
        Flow:
        1. Calculate base bid based on strategy
        2. Apply device adjustment
        3. Apply hour adjustment
        4. Apply quality score modifier
        5. Apply seasonal adjustment
        """
        
        # Use ML if available
        if self.use_ml and context:
            base_bid = self._ml_bid(context)
        else:
            # Strategy-based bidding
            cvr = cvr_hat if cvr_hat is not None else self.historical_cvr
            value = value_hat if value_hat is not None else self.historical_value

            if self.strategy == "target_cpa":
                base_bid = self.target_cpa * cvr
            elif self.strategy == "target_roas":
                base_bid = (value / self.target_roas) * cvr
            elif self.strategy == "maximize_clicks":
                base_bid = self.base_bid * 1.25
            elif self.strategy == "maximize_conversions":
                base_bid = self.base_bid * (1 + cvr * 10)
            else:  # manual_cpc
                base_bid = self.base_bid
        
        # Apply modifiers if context provided
        if context:
            # Device adjustment
            device_mult = self.device_adjustments.get(context.device, 1.0)
            base_bid *= device_mult
            
            # Hour adjustment
            hour_mult = self.hour_adjustments.get(context.hour, 1.0)
            base_bid *= hour_mult
            
            # Quality Score adjustment (higher QS = higher bid for same position)
            qs_mult = 0.7 + (context.quality_score / 10) * 0.6  # 0.7 to 1.3 range
            base_bid *= qs_mult
            
            # Seasonal adjustment
            # Create a date from context for seasonality
            date = datetime(2024, 1, 1) + pd.Timedelta(days=context.day_of_week)
            seasonal_mult = self.seasonality.get_multiplier(date)
            base_bid *= seasonal_mult
            
            # Competition adjustment
            if context.competitor_density > 0.7:
                base_bid *= 1.1  # Bid higher in competitive auctions
            elif context.competitor_density < 0.3:
                base_bid *= 0.9  # Bid lower when less competition
        
        return max(0.10, base_bid)  # Minimum bid of $0.10
    
    def get_bid_explanation(self, base_bid: float, context: BidContext) -> Dict:
        """
        Educational function: explain how bid was calculated.
        Shows all the modifiers that were applied.
        """
        explanation = {
            'base_bid': round(base_bid, 2),
            'modifiers': []
        }
        
        # Device adjustment
        device_mult = self.device_adjustments.get(context.device, 1.0)
        if device_mult != 1.0:
            explanation['modifiers'].append({
                'type': 'Device',
                'value': context.device,
                'multiplier': device_mult,
                'reason': f"{'+' if device_mult > 1 else ''}{(device_mult-1)*100:.0f}% for {context.device}"
            })
        
        # Hour adjustment
        hour_mult = self.hour_adjustments.get(context.hour, 1.0)
        if hour_mult != 1.0:
            explanation['modifiers'].append({
                'type': 'Hour',
                'value': context.hour,
                'multiplier': hour_mult,
                'reason': f"{'+' if hour_mult > 1 else ''}{(hour_mult-1)*100:.0f}% for hour {context.hour}"
            })
        
        # Quality Score
        qs_mult = 0.7 + (context.quality_score / 10) * 0.6
        explanation['modifiers'].append({
            'type': 'Quality Score',
            'value': context.quality_score,
            'multiplier': qs_mult,
            'reason': f"QS {context.quality_score}/10 → {(qs_mult-1)*100:+.0f}% adjustment"
        })
        
        # Calculate final bid
        final_bid = base_bid
        total_multiplier = 1.0
        for mod in explanation['modifiers']:
            final_bid *= mod['multiplier']
            total_multiplier *= mod['multiplier']
        
        explanation['final_bid'] = round(final_bid, 2)
        explanation['total_multiplier'] = round(total_multiplier, 3)
        explanation['total_change_pct'] = round((total_multiplier - 1) * 100, 1)
        
        return explanation
    
    def train_ml_models(self, historical_data: List[Dict]):
        """Train ML models for predictive bidding."""
        if not ML_AVAILABLE or not historical_data:
            print("ML training skipped.")
            return

        df = pd.DataFrame(historical_data)
        features = ['hour', 'day_of_week', 'is_mobile', 'quality_score', 'competitor_density', 
                   'historical_ctr', 'is_exact', 'day_of_month', 'is_holiday']
        
        # Feature engineering
        df['is_mobile'] = (df['device'] == 'mobile').astype(int)
        df['is_exact'] = (df['match_type'] == 'exact').astype(int)
        
        # Add dummy data if columns missing
        for col in features:
            if col not in df.columns:
                df[col] = 0
        
        X = df[features]
        y_ctr = df['clicks'] / df['impressions']
        y_cvr = df['conversions'] / df['clicks'].replace(0, 1)

        # Train CTR model
        self.ctr_model = lgb.LGBMRegressor(random_state=42, verbose=-1)
        self.ctr_model.fit(X, y_ctr)

        # Train CVR model
        self.cvr_model = lgb.LGBMRegressor(random_state=42, verbose=-1)
        self.cvr_model.fit(X, y_cvr)
        
        print("✅ ML bidding models trained successfully.")
