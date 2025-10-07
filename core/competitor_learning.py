# /core/competitor_learning.py
"""
Competitor Learning Module
Models how competitors adjust their bidding strategies over time based on performance.
Makes the simulation more realistic by having dynamic competition.
"""

from typing import Dict, List
from dataclasses import dataclass
import math
import hashlib

@dataclass
class CompetitorProfile:
    """Represents a competitor in the auction."""
    id: str
    base_bid: float
    quality_score: float
    aggressiveness: float  # 0.0 to 1.0
    learning_rate: float   # How fast they adjust
    win_rate: float = 0.0
    avg_position: float = 5.0
    total_spend: float = 0.0
    total_clicks: float = 0.0
    strategy: str = "balanced"  # conservative, balanced, aggressive

class CompetitorLearningEngine:
    """
    Simulates intelligent competitors who learn and adapt their bidding strategies.
    
    Key behaviors:
    1. Increase bids when losing auctions
    2. Decrease bids when winning too often (to save budget)
    3. React to advertiser's bid changes
    4. Have different strategies (conservative, balanced, aggressive)
    """
    
    def __init__(self, num_competitors: int = 10, market_competition: float = 0.7):
        self.competitors: Dict[str, CompetitorProfile] = {}
        self.num_competitors = num_competitors
        self.market_competition = market_competition
        self.auction_history: List[Dict] = []
        
        # Initialize competitors with diverse profiles
        self._initialize_competitors()
    
    def _initialize_competitors(self):
        """Create diverse competitor profiles."""
        strategies = ["conservative", "balanced", "aggressive"]
        
        for i in range(self.num_competitors):
            # Distribute competitors across strategies
            strategy = strategies[i % 3]
            
            # Strategy affects base characteristics
            if strategy == "conservative":
                base_bid = 0.5 + (i * 0.1)
                aggressiveness = 0.3 + (i * 0.05)
                learning_rate = 0.1
            elif strategy == "aggressive":
                base_bid = 1.5 + (i * 0.2)
                aggressiveness = 0.7 + (i * 0.05)
                learning_rate = 0.3
            else:  # balanced
                base_bid = 1.0 + (i * 0.15)
                aggressiveness = 0.5 + (i * 0.05)
                learning_rate = 0.2
            
            # Quality score distribution (most are 5-7)
            quality_score = 5.0 + (math.sin(i) * 2)  # Deterministic 3-7 range
            quality_score = max(3.0, min(7.0, quality_score))
            
            self.competitors[f"comp_{i}"] = CompetitorProfile(
                id=f"comp_{i}",
                base_bid=base_bid,
                quality_score=quality_score,
                aggressiveness=aggressiveness,
                learning_rate=learning_rate,
                strategy=strategy
            )
    
    def record_auction(self, winner_id: str, winner_bid: float, advertiser_bid: float, 
                      all_bids: List[float], position: int):
        """
        Record auction results for learning.
        
        Args:
            winner_id: ID of auction winner
            winner_bid: Winning bid amount
            advertiser_bid: Advertiser's bid
            all_bids: All bids in auction
            position: Position won
        """
        auction_result = {
            'winner_id': winner_id,
            'winner_bid': winner_bid,
            'advertiser_bid': advertiser_bid,
            'avg_bid': sum(all_bids) / len(all_bids) if all_bids else 0,
            'position': position
        }
        
        self.auction_history.append(auction_result)
        
        # Update competitor stats
        for comp_id, competitor in self.competitors.items():
            if comp_id == winner_id:
                competitor.win_rate = (competitor.win_rate * 0.9) + (1.0 * 0.1)  # Won
                competitor.avg_position = (competitor.avg_position * 0.9) + (position * 0.1)
            else:
                competitor.win_rate = competitor.win_rate * 0.9  # Lost
    
    def adjust_bids(self, advertiser_bid: float, day: int) -> Dict[str, float]:
        """
        Competitors adjust their bids based on performance and advertiser behavior.
        
        Returns:
            Dictionary of competitor_id -> adjusted_bid
        """
        adjusted_bids = {}
        
        for comp_id, competitor in self.competitors.items():
            # Start with base bid
            current_bid = competitor.base_bid
            
            # 1. Adjust based on win rate
            if competitor.win_rate < 0.2:
                # Losing too much - increase bid
                bid_increase = competitor.learning_rate * competitor.aggressiveness * 0.3
                current_bid *= (1.0 + bid_increase)
            elif competitor.win_rate > 0.6:
                # Winning too much - can reduce bid to save money
                bid_decrease = competitor.learning_rate * 0.2
                current_bid *= (1.0 - bid_decrease)
            
            # 2. React to advertiser's bid (competitive response)
            if advertiser_bid > current_bid:
                # Advertiser is bidding higher
                bid_gap = advertiser_bid - current_bid
                competitive_response = bid_gap * competitor.aggressiveness * 0.5
                current_bid += competitive_response
            
            # 3. Adjust based on position
            if competitor.avg_position > 3.0:
                # Not getting good positions - bid higher
                position_adjustment = (competitor.avg_position - 3.0) * 0.1
                current_bid *= (1.0 + position_adjustment)
            
            # 4. Strategy-specific behavior
            if competitor.strategy == "aggressive":
                # Aggressive competitors increase bids over time
                current_bid *= (1.0 + (day * 0.01))
            elif competitor.strategy == "conservative":
                # Conservative competitors decrease bids over time
                current_bid *= (1.0 - (day * 0.005))
            
            # 5. Market competition effect
            current_bid *= self.market_competition
            
            # 6. Random fluctuation (small, deterministic)
            # Use deterministic hash instead of Python's random hash()
            comp_hash = int(hashlib.sha256(comp_id.encode()).hexdigest(), 16) % 1000
            fluctuation = math.sin(day + comp_hash) * 0.05  # -5% to +5%
            current_bid *= (1.0 + fluctuation)
            
            # Update base bid for next time (learning)
            competitor.base_bid = (competitor.base_bid * 0.8) + (current_bid * 0.2)
            
            # Ensure bid stays in reasonable range
            adjusted_bids[comp_id] = max(0.10, min(10.0, current_bid))
        
        return adjusted_bids
    
    def get_competitor_insights(self) -> Dict:
        """Get insights about competitor behavior for educational purposes."""
        if not self.auction_history:
            return {'message': 'No auction data yet'}
        
        insights = {
            'total_auctions': len(self.auction_history),
            'avg_competition_level': sum(c.base_bid for c in self.competitors.values()) / len(self.competitors),
            'competitor_strategies': {
                'conservative': len([c for c in self.competitors.values() if c.strategy == 'conservative']),
                'balanced': len([c for c in self.competitors.values() if c.strategy == 'balanced']),
                'aggressive': len([c for c in self.competitors.values() if c.strategy == 'aggressive'])
            },
            'top_competitors': []
        }
        
        # Find top 3 competitors by win rate
        sorted_comps = sorted(self.competitors.values(), key=lambda x: x.win_rate, reverse=True)
        for comp in sorted_comps[:3]:
            insights['top_competitors'].append({
                'id': comp.id,
                'strategy': comp.strategy,
                'win_rate': round(comp.win_rate * 100, 1),
                'avg_position': round(comp.avg_position, 1),
                'current_bid': round(comp.base_bid, 2)
            })
        
        return insights
    
    def simulate_market_shift(self, shift_type: str):
        """
        Simulate market changes (e.g., new competitor enters, budget cuts).
        
        Args:
            shift_type: 'new_entrant', 'budget_cuts', 'increased_competition'
        """
        if shift_type == 'new_entrant':
            # New aggressive competitor enters
            new_id = f"comp_new_{len(self.competitors)}"
            self.competitors[new_id] = CompetitorProfile(
                id=new_id,
                base_bid=2.0,
                quality_score=6.0,
                aggressiveness=0.9,
                learning_rate=0.4,
                strategy='aggressive'
            )
        
        elif shift_type == 'budget_cuts':
            # All competitors reduce bids by 20%
            for competitor in self.competitors.values():
                competitor.base_bid *= 0.8
        
        elif shift_type == 'increased_competition':
            # All competitors become more aggressive
            for competitor in self.competitors.values():
                competitor.aggressiveness = min(1.0, competitor.aggressiveness * 1.3)
