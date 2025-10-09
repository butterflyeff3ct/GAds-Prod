# /features/attribution.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import math

class AttributionModel(Enum):
    LAST_CLICK = "last_click"
    FIRST_CLICK = "first_click"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"

@dataclass
class TouchPoint:
    timestamp: datetime
    channel: str
    campaign_id: str
    ad_group_id: str
    keyword_id: Optional[str]
    ad_id: str
    cost: float
    device: str
    position: int
    interaction_type: str

@dataclass
class ConversionEvent:
    timestamp: datetime
    conversion_type: str
    value: float

@dataclass
class ConversionPath:
    user_id: str
    touchpoints: List[TouchPoint]
    conversion: Optional[ConversionEvent] = None

class AttributionEngine:
    """
    Complete multi-touch attribution engine supporting all major models.
    Educational implementation showing how different attribution models work.
    """
    
    def __init__(self, model: AttributionModel = AttributionModel.LAST_CLICK):
        self.model = model
        self.time_decay_half_life = 7  # days

    def attribute_conversion(self, path: ConversionPath) -> Dict[str, float]:
        """
        Attribute conversion value across touchpoints using the selected model.
        
        Returns:
            Dictionary mapping touchpoint keys to attributed value
        """
        if not path.conversion or not path.touchpoints:
            return {}
        
        total_value = path.conversion.value
        num_touchpoints = len(path.touchpoints)
        touchpoint_keys = [f"{tp.campaign_id}_{tp.keyword_id or 'none'}" for tp in path.touchpoints]
        
        attributions = {key: 0.0 for key in touchpoint_keys}

        if self.model == AttributionModel.LAST_CLICK:
            # 100% credit to last touchpoint
            attributions[touchpoint_keys[-1]] = total_value
            
        elif self.model == AttributionModel.FIRST_CLICK:
            # 100% credit to first touchpoint
            attributions[touchpoint_keys[0]] = total_value
            
        elif self.model == AttributionModel.LINEAR:
            # Equal credit to all touchpoints
            credit = total_value / num_touchpoints
            for key in touchpoint_keys:
                attributions[key] += credit
                
        elif self.model == AttributionModel.TIME_DECAY:
            # More recent touchpoints get more credit (exponential decay)
            if not path.conversion:
                return attributions
            
            conversion_time = path.conversion.timestamp
            weights = []
            
            for tp in path.touchpoints:
                days_before_conversion = (conversion_time - tp.timestamp).days
                # Exponential decay: weight = 2^(-days / half_life)
                weight = math.pow(2, -days_before_conversion / self.time_decay_half_life)
                weights.append(weight)
            
            total_weight = sum(weights)
            
            for i, key in enumerate(touchpoint_keys):
                credit = total_value * (weights[i] / total_weight)
                attributions[key] += credit
                
        elif self.model == AttributionModel.POSITION_BASED:
            # 40% to first, 40% to last, 20% distributed among middle
            if num_touchpoints == 1:
                attributions[touchpoint_keys[0]] = total_value
            elif num_touchpoints == 2:
                # Split 50/50
                attributions[touchpoint_keys[0]] += total_value * 0.5
                attributions[touchpoint_keys[1]] += total_value * 0.5
            else:
                # 40% first, 40% last, 20% middle
                attributions[touchpoint_keys[0]] += total_value * 0.4
                attributions[touchpoint_keys[-1]] += total_value * 0.4
                
                middle_credit = total_value * 0.2 / (num_touchpoints - 2)
                for i in range(1, num_touchpoints - 1):
                    attributions[touchpoint_keys[i]] += middle_credit
                    
        elif self.model == AttributionModel.DATA_DRIVEN:
            # Simplified data-driven: weighs based on position AND conversion rate
            # In reality, this uses machine learning on historical data
            weights = []
            
            for i, tp in enumerate(path.touchpoints):
                # Position factor (U-shaped: first and last are important)
                if i == 0:
                    position_weight = 1.5
                elif i == num_touchpoints - 1:
                    position_weight = 2.0  # Last touch most important
                else:
                    # Middle touches get less weight
                    position_weight = 0.5 + (i / num_touchpoints)
                
                # Channel effectiveness (simplified)
                channel_weights = {
                    'search': 1.2,
                    'display': 0.8,
                    'social': 0.9,
                    'email': 1.0
                }
                channel_weight = channel_weights.get(tp.channel.lower(), 1.0)
                
                # Interaction type weight
                interaction_weights = {
                    'click': 1.0,
                    'impression': 0.3,
                    'view': 0.5
                }
                interaction_weight = interaction_weights.get(tp.interaction_type.lower(), 1.0)
                
                # Combined weight
                total_weight = position_weight * channel_weight * interaction_weight
                weights.append(total_weight)
            
            total_weight = sum(weights)
            
            for i, key in enumerate(touchpoint_keys):
                credit = total_value * (weights[i] / total_weight)
                attributions[key] += credit
        
        return attributions

    def compare_attribution_models(self, paths: List[ConversionPath]) -> Dict:
        """
        Compare how different attribution models credit the same conversion paths.
        Great for educational purposes to show model differences.
        """
        results = {}
        
        for model in AttributionModel:
            original_model = self.model
            self.model = model
            
            model_attribution = {}
            for path in paths:
                if not path.conversion:
                    continue
                attribution = self.attribute_conversion(path)
                for key, value in attribution.items():
                    model_attribution[key] = model_attribution.get(key, 0) + value
            
            results[model.value] = model_attribution
            self.model = original_model
        
        return results
    
    def calculate_attribution_metrics(self, paths: List[ConversionPath]) -> Dict:
        """
        Calculate aggregate metrics about conversion paths.
        
        Returns metrics like:
        - Average days to conversion
        - Average touchpoints per conversion
        - Top converting path patterns
        - Channel contribution
        """
        total_conversions = sum(1 for path in paths if path.conversion)
        if not total_conversions:
            return {
                'avg_days_to_conversion': 0,
                'avg_touchpoints': 0,
                'top_converting_paths': [],
                'channel_contribution': {}
            }

        total_days = 0
        total_touchpoints = 0
        path_patterns = {}
        channel_stats = {}
        
        for path in paths:
            if not path.conversion:
                continue
            
            # Days to conversion
            days = (path.conversion.timestamp - path.touchpoints[0].timestamp).days
            total_days += days
            
            # Touchpoints per conversion
            total_touchpoints += len(path.touchpoints)
            
            # Path patterns
            channels = '->'.join([tp.channel for tp in path.touchpoints])
            if channels not in path_patterns:
                path_patterns[channels] = {'count': 0, 'value': 0}
            path_patterns[channels]['count'] += 1
            path_patterns[channels]['value'] += path.conversion.value
            
            # Channel contribution
            for tp in path.touchpoints:
                if tp.channel not in channel_stats:
                    channel_stats[tp.channel] = {'touches': 0, 'conversions': 0, 'value': 0}
                channel_stats[tp.channel]['touches'] += 1
                channel_stats[tp.channel]['conversions'] += 1
                channel_stats[tp.channel]['value'] += path.conversion.value

        return {
            'avg_days_to_conversion': total_days / total_conversions,
            'avg_touchpoints': total_touchpoints / total_conversions,
            'top_converting_paths': sorted(
                path_patterns.items(), 
                key=lambda x: x[1]['value'], 
                reverse=True
            )[:10],
            'channel_contribution': channel_stats,
            'total_conversions': total_conversions,
            'total_value': sum(p.conversion.value for p in paths if p.conversion)
        }
    
    def get_model_explanation(self) -> str:
        """Return educational explanation of the current attribution model."""
        explanations = {
            AttributionModel.LAST_CLICK: (
                "**Last Click Attribution**\n\n"
                "Gives 100% credit to the final touchpoint before conversion.\n\n"
                "✅ Simple and clear\n"
                "❌ Ignores influence of earlier touchpoints\n"
                "📚 Best for: Short sales cycles, direct response campaigns"
            ),
            AttributionModel.FIRST_CLICK: (
                "**First Click Attribution**\n\n"
                "Gives 100% credit to the first touchpoint in the customer journey.\n\n"
                "✅ Values awareness and discovery\n"
                "❌ Ignores nurturing touchpoints\n"
                "📚 Best for: Brand awareness campaigns, top-of-funnel analysis"
            ),
            AttributionModel.LINEAR: (
                "**Linear Attribution**\n\n"
                "Distributes credit equally across all touchpoints.\n\n"
                "✅ Fair and balanced view\n"
                "❌ Doesn't reflect different touchpoint importance\n"
                "📚 Best for: Understanding full customer journey, multi-channel campaigns"
            ),
            AttributionModel.TIME_DECAY: (
                "**Time Decay Attribution**\n\n"
                "Gives more credit to touchpoints closer to conversion (exponential decay).\n\n"
                "✅ Reflects recency bias in decision-making\n"
                "❌ May undervalue early awareness touchpoints\n"
                "📚 Best for: Campaigns with clear decision moments, retail"
            ),
            AttributionModel.POSITION_BASED: (
                "**Position-Based Attribution (U-Shaped)**\n\n"
                "Gives 40% credit to first touch, 40% to last touch, 20% to middle touches.\n\n"
                "✅ Values both awareness and conversion drivers\n"
                "✅ Recognizes importance of journey endpoints\n"
                "📚 Best for: Balanced view of awareness and conversion"
            ),
            AttributionModel.DATA_DRIVEN: (
                "**Data-Driven Attribution**\n\n"
                "Uses actual conversion data to determine credit distribution algorithmically.\n\n"
                "✅ Based on real performance data\n"
                "✅ Adapts to your specific customer behavior\n"
                "📚 Best for: Large datasets, mature marketing programs"
            )
        }
        return explanations.get(self.model, "Unknown model")


# Educational example usage
def create_sample_conversion_path() -> ConversionPath:
    """Create a sample conversion path for testing and education."""
    touchpoints = [
        TouchPoint(
            timestamp=datetime(2024, 1, 1, 10, 0),
            channel='search',
            campaign_id='camp_1',
            ad_group_id='ag_1',
            keyword_id='kw_shoes',
            ad_id='ad_1',
            cost=1.50,
            device='desktop',
            position=2,
            interaction_type='click'
        ),
        TouchPoint(
            timestamp=datetime(2024, 1, 3, 14, 30),
            channel='display',
            campaign_id='camp_2',
            ad_group_id='ag_2',
            keyword_id=None,
            ad_id='ad_2',
            cost=0.80,
            device='mobile',
            position=1,
            interaction_type='impression'
        ),
        TouchPoint(
            timestamp=datetime(2024, 1, 5, 9, 15),
            channel='search',
            campaign_id='camp_1',
            ad_group_id='ag_1',
            keyword_id='kw_running_shoes',
            ad_id='ad_3',
            cost=2.20,
            device='desktop',
            position=1,
            interaction_type='click'
        )
    ]
    
    conversion = ConversionEvent(
        timestamp=datetime(2024, 1, 5, 9, 30),
        conversion_type='purchase',
        value=100.0
    )
    
    return ConversionPath(
        user_id='user_123',
        touchpoints=touchpoints,
        conversion=conversion
    )
