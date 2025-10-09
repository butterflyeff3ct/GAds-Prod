# /features/targeting.py
from typing import List, Dict, Optional
from dataclasses import dataclass
import random

@dataclass
class GeoTarget:
    location_id: str
    location_name: str
    bid_modifier: float

@dataclass
class AudienceSegment:
    segment_id: str
    segment_name: str
    bid_modifier: float

class TargetingEngine:
    def __init__(self):
        self.geo_database = {
            '2840': {'name': 'United States'}, '2124': {'name': 'Canada'},
            '2826': {'name': 'United Kingdom'}
        }
        self.audience_database = {
            'all_visitors': {'name': 'All Website Visitors'},
            'cart_abandoners': {'name': 'Cart Abandoners'}
        }
        self.active_targets = {'geo': [], 'audience': [], 'device': [], 'daypart': []}

    def add_geo_target(self, location_id: str, bid_modifier: float = 1.0) -> Optional[GeoTarget]:
        if location_id not in self.geo_database: return None
        target = GeoTarget(
            location_id=location_id,
            location_name=self.geo_database[location_id]['name'],
            bid_modifier=bid_modifier
        )
        self.active_targets['geo'].append(target)
        return target

    def add_audience_target(self, segment_id: str, bid_modifier: float = 1.0) -> Optional[AudienceSegment]:
        if segment_id not in self.audience_database: return None
        target = AudienceSegment(
            segment_id=segment_id,
            segment_name=self.audience_database[segment_id]['name'],
            bid_modifier=bid_modifier
        )
        self.active_targets['audience'].append(target)
        return target

    def calculate_total_bid_modifier(self, geo: str, device: str, hour: int, day_of_week: int, user_audiences: List[str]) -> float:
        modifier = 1.0
        # This is a simplified calculation. A full implementation would check against active_targets
        if geo != 'US': modifier *= 0.9
        if device == 'mobile': modifier *= 0.85
        if 'cart_abandoners' in user_audiences: modifier *= 1.3
        
        return min(10.0, max(0.1, modifier))