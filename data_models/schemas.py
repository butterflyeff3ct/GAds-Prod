# /data_models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, time
from enum import Enum

class Status(str, Enum):
    ENABLED = "enabled"
    PAUSED = "paused"
    REMOVED = "removed"

class BiddingStrategy(str, Enum):
    MANUAL_CPC = "manual_cpc"
    TARGET_CPA = "target_cpa"
    TARGET_ROAS = "target_roas"
    MAXIMIZE_CLICKS = "maximize_clicks"
    MAXIMIZE_CONVERSIONS = "maximize_conversions"
    TARGET_IMPRESSION_SHARE = "target_impression_share"
    MAXIMIZE_CONVERSION_VALUE = "maximize_conversion_value"

class MatchType(str, Enum):
    EXACT = "exact"
    PHRASE = "phrase"
    BROAD = "broad"

class AdSchedule(BaseModel):
    """Ad scheduling (dayparting) configuration."""
    enabled: bool = False
    monday: List[int] = Field(default_factory=lambda: list(range(24)))
    tuesday: List[int] = Field(default_factory=lambda: list(range(24)))
    wednesday: List[int] = Field(default_factory=lambda: list(range(24)))
    thursday: List[int] = Field(default_factory=lambda: list(range(24)))
    friday: List[int] = Field(default_factory=lambda: list(range(24)))
    saturday: List[int] = Field(default_factory=lambda: list(range(24)))
    sunday: List[int] = Field(default_factory=lambda: list(range(24)))
    
    def is_active(self, day_of_week: int, hour: int) -> bool:
        """Check if ads should show at this day/hour (0=Monday, 6=Sunday)."""
        if not self.enabled:
            return True
        
        day_schedules = [
            self.monday, self.tuesday, self.wednesday, self.thursday,
            self.friday, self.saturday, self.sunday
        ]
        
        if 0 <= day_of_week < 7:
            return hour in day_schedules[day_of_week]
        return True
    
    def get_bid_adjustment(self, day_of_week: int, hour: int) -> float:
        """Get bid adjustment for specific day/hour (can be extended later)."""
        # For now, just on/off. Later can add bid modifiers per time slot
        return 1.0 if self.is_active(day_of_week, hour) else 0.0

class Campaign(BaseModel):
    id: str
    name: str
    status: Status = Status.ENABLED
    daily_budget: float = Field(gt=0)
    bidding_strategy: BiddingStrategy = BiddingStrategy.MANUAL_CPC
    
    # Networks
    networks: List[str] = Field(default_factory=lambda: ["google_search"])
    
    # Targeting
    geo_targets: List[str] = Field(default_factory=list)
    geo_bid_adjustments: Dict[str, float] = Field(default_factory=dict)  # NEW
    device_bid_adjustments: Dict[str, float] = Field(default_factory=dict)
    
    # Bidding targets
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    target_impression_share: Optional[float] = None  # NEW
    target_location: Optional[str] = None  # NEW: "anywhere", "top_of_page", "absolute_top"
    
    # Ad schedule
    ad_schedule: AdSchedule = Field(default_factory=AdSchedule)  # NEW
    
    # Negative keywords (campaign level)
    negative_keywords: List[str] = Field(default_factory=list)  # NEW

class AdGroup(BaseModel):
    id: str
    campaign_id: str
    name: str
    status: Status = Status.ENABLED
    default_bid: float = Field(gt=0, default=1.0)
    
    # Negative keywords (ad group level)
    negative_keywords: List[str] = Field(default_factory=list)  # NEW

class Keyword(BaseModel):
    id: str
    ad_group_id: str
    text: str
    match_type: MatchType = MatchType.BROAD
    status: Status = Status.ENABLED
    cpc_bid: Optional[float] = None  # NEW: Keyword-level bid (overrides ad group default)
    final_url: Optional[str] = None
    quality_score: Optional[int] = None
    
    def get_bid(self, ad_group_default: float) -> float:
        """Get effective bid (keyword-level or ad group default)."""
        return self.cpc_bid if self.cpc_bid is not None else ad_group_default

class AdExtension(BaseModel):
    """Ad extension model."""
    type: str  # sitelink, callout, structured_snippet, call, location, etc.
    text: str
    description: Optional[str] = None
    final_url: Optional[str] = None
    status: Status = Status.ENABLED

class Ad(BaseModel):
    id: str
    ad_group_id: str
    status: Status = Status.ENABLED
    headlines: List[str] = Field(min_items=1)
    descriptions: List[str] = Field(min_items=1)
    final_url: str
    
    # Ad extensions
    sitelinks: List[AdExtension] = Field(default_factory=list)  # NEW
    callouts: List[str] = Field(default_factory=list)  # NEW
    structured_snippets: Dict[str, List[str]] = Field(default_factory=dict)  # NEW
    
    def get_all_extensions(self) -> List[AdExtension]:
        """Get all extensions for this ad."""
        extensions = list(self.sitelinks)
        
        # Convert callouts to extensions
        for callout in self.callouts:
            extensions.append(AdExtension(type="callout", text=callout))
        
        # Convert structured snippets
        for header, values in self.structured_snippets.items():
            extensions.append(AdExtension(
                type="structured_snippet",
                text=header,
                description=", ".join(values)
            ))
        
        return extensions

class AuctionResult(BaseModel):
    query: str
    matched_keyword: str
    ad_id: str
    ad_rank: float
    cpc: float
    position: int
    impressions: int
    clicks: int
    conversions: int
    cost: float
    revenue: float
    timestamp: Optional[datetime] = None
    device: str = "desktop"
    geo: str = "US"
    network: str = "google_search"
    hour: int = 12
    day_of_week: int = 0
