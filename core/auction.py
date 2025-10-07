# /core/auction.py
from typing import List, Dict, Tuple
from data_models.schemas import AuctionResult, Ad, Keyword
from datetime import datetime
import math
from dataclasses import dataclass

@dataclass
class AuctionSignals:
    device_type: str
    geo_location: str
    user_intent: float
    time_of_day: int
    day_of_week: int
    is_remarketing: bool
    query_length: int
    competitor_presence: float

@dataclass
class CompetitorBid:
    bid: float
    quality_score: float

class AuctionEngine:
    """
    Deterministic auction engine that models Google Ads GSP auction mechanics.
    Uses logical formulas instead of randomization for educational purposes.
    """
    
    def __init__(self, num_slots: int = 4, price_increment: float = 0.01):
        self.num_slots = num_slots
        self.price_increment = price_increment
        self.competitor_pool_size = 10
        
        # Industry-specific competition levels (can be configured per campaign)
        self.industry_competition = {
            'finance': 0.9,
            'insurance': 0.85,
            'legal': 0.8,
            'ecommerce': 0.7,
            'b2b': 0.6,
            'education': 0.5,
            'default': 0.65
        }
        
        # Hourly search volume distribution (realistic pattern)
        self.hourly_distribution = [
            0.02, 0.01, 0.01, 0.01, 0.02, 0.03,  # 0-5 AM
            0.04, 0.05, 0.06, 0.07, 0.08, 0.08,  # 6-11 AM
            0.07, 0.07, 0.06, 0.06, 0.07, 0.08,  # 12-5 PM
            0.07, 0.06, 0.05, 0.04, 0.03, 0.02   # 6-11 PM
        ]

    def _generate_signals(self, query: str, hour: int, device: str, geo: str, 
                         industry: str = 'default', day_of_week: int = 0) -> AuctionSignals:
        """Generate deterministic auction signals based on query characteristics."""
        
        # Commercial intent scoring (deterministic based on query terms)
        commercial_terms = {
            'buy': 0.9, 'purchase': 0.85, 'price': 0.8, 'cheap': 0.75,
            'best': 0.7, 'review': 0.65, 'compare': 0.6, 'deal': 0.75,
            'discount': 0.7, 'sale': 0.75, 'shop': 0.8, 'order': 0.85,
            'how': 0.3, 'what': 0.25, 'why': 0.2, 'where': 0.35
        }
        
        query_lower = query.lower()
        intent_scores = [score for term, score in commercial_terms.items() 
                        if term in query_lower]
        intent_score = max(intent_scores) if intent_scores else 0.4
        
        # Query complexity affects competition
        query_words = len(query.split())
        complexity_factor = min(1.0, 0.5 + (query_words * 0.1))
        
        # Competition presence (deterministic based on query and industry)
        base_competition = self.industry_competition.get(industry, 
                                                        self.industry_competition['default'])
        competitor_presence = min(0.95, base_competition * intent_score * complexity_factor)
        
        # Remarketing likelihood (deterministic)
        is_remarketing = intent_score > 0.6 and query_words >= 3
        
        return AuctionSignals(
            device_type=device,
            geo_location=geo,
            user_intent=intent_score,
            time_of_day=hour,
            day_of_week=day_of_week,
            is_remarketing=is_remarketing,
            query_length=query_words,
            competitor_presence=competitor_presence
        )

    def _generate_competitor_bids(self, signals: AuctionSignals, 
                                 advertiser_bid: float) -> List[CompetitorBid]:
        """Generate deterministic competitor bids based on auction signals."""
        
        competitors = []
        num_competitors = int(self.competitor_pool_size * signals.competitor_presence)
        
        # Competitor strength distribution (deterministic)
        for i in range(num_competitors):
            # Position in market (0 = weakest, 1 = strongest)
            market_position = i / max(1, num_competitors - 1)
            
            # Strength based on position (bell curve)
            strength = 0.3 + (0.7 * math.sin(market_position * math.pi))
            
            # Base bid influenced by advertiser's bid (market awareness)
            market_aware_base = advertiser_bid * (0.7 + (market_position * 0.6))
            
            # Intent-based adjustment
            intent_multiplier = 0.8 + (signals.user_intent * 0.4)
            
            # Time-of-day multiplier (peak hours = higher bids)
            hour_multiplier = 0.9 + (self.hourly_distribution[signals.time_of_day] * 2)
            
            # Calculate final bid
            bid = market_aware_base * strength * intent_multiplier * hour_multiplier
            
            # Quality score based on strength
            quality_score = 3 + (strength * 7)
            
            competitors.append(CompetitorBid(bid=bid, quality_score=quality_score))
        
        return competitors

    def _calculate_expected_performance(self, ctr: float, cvr: float, 
                                       position: int, signals: AuctionSignals) -> Tuple[int, int, int]:
        """
        Calculate deterministic clicks and conversions based on rates and context.
        No randomization - uses expected values with position adjustments.
        """
        
        # Position-based CTR multiplier (top positions get higher CTR)
        position_multipliers = {
            1: 1.0,      # Top position = 100% of base CTR
            2: 0.75,     # 25% drop
            3: 0.55,     # Further decline
            4: 0.40      # Bottom position
        }
        adjusted_ctr = ctr * position_multipliers.get(position, 0.3)
        
        # Device adjustment
        device_multipliers = {'mobile': 0.85, 'desktop': 1.0, 'tablet': 0.9}
        adjusted_ctr *= device_multipliers.get(signals.device_type, 1.0)
        
        # Hour of day adjustment
        hour_factor = 0.8 + (self.hourly_distribution[signals.time_of_day] * 4)
        adjusted_ctr *= hour_factor
        
        # Remarketing boost
        if signals.is_remarketing:
            adjusted_ctr *= 1.3
            cvr *= 1.5
        
        # For educational simulator: generate consistent impressions based on query
        # Increased multiplier to generate realistic impression volumes
        base_impressions = max(1, int(100 * signals.user_intent * signals.competitor_presence))
        
        # Calculate expected clicks (deterministic, not probabilistic)
        expected_clicks = base_impressions * adjusted_ctr
        clicks = max(0, int(round(expected_clicks)))
        
        # Calculate expected conversions
        expected_conversions = clicks * cvr
        conversions = max(0, int(round(expected_conversions)))
        
        return base_impressions, clicks, conversions

    def run_auction(self, query: str, ads: List[Ad], bids: List[float], 
                   qs_scores: List[float], base_ctr: List[float], 
                   cvr_preds: List[float], hour: int, device: str, geo: str,
                   revenue_per_conv: float = 100.0, industry: str = 'default',
                   day_of_week: int = 0) -> List[AuctionResult]:
        """
        Run deterministic GSP (Generalized Second Price) auction.
        Returns consistent results for the same inputs.
        """
        
        # Generate auction signals
        signals = self._generate_signals(query, hour, device, geo, industry, day_of_week)
        
        # Generate competitor bids
        competitor_bids = self._generate_competitor_bids(signals, max(bids) if bids else 1.0)
        
        # Combine advertiser and competitor data
        all_bids = bids + [c.bid for c in competitor_bids]
        all_qs = qs_scores + [c.quality_score for c in competitor_bids]
        
        # Calculate Ad Ranks (bid × quality score)
        ad_ranks = [all_bids[i] * all_qs[i] for i in range(len(all_bids))]
        
        # Sort by Ad Rank (highest first)
        eligible = sorted(
            [(i, rank) for i, rank in enumerate(ad_ranks) if rank > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        if not eligible:
            return []
        
        results = []
        for pos, (idx, rank) in enumerate(eligible[:self.num_slots]):
            # Only return results for advertiser's ads (not competitors)
            if idx >= len(ads):
                continue
            
            # Calculate actual CPC using GSP formula
            # CPC = (next bidder's Ad Rank / your quality score) + $0.01
            if pos + 1 < len(eligible):
                next_bidder_rank = eligible[pos + 1][1]
                cpc = (next_bidder_rank / all_qs[idx]) + self.price_increment
            else:
                # No one below you, you pay minimum
                cpc = self.price_increment
            
            # Cap CPC at actual bid (can't pay more than your max)
            cpc = min(cpc, all_bids[idx])
            
            # Calculate performance deterministically
            impressions, clicks, conversions = self._calculate_expected_performance(
                base_ctr[idx], cvr_preds[idx], pos + 1, signals
            )
            
            # Calculate costs and revenue
            cost = cpc * clicks
            revenue = conversions * revenue_per_conv
            
            results.append(AuctionResult(
                query=query,
                matched_keyword=ads[idx].id,
                ad_id=ads[idx].id,
                ad_rank=round(rank, 2),
                cpc=round(cpc, 2),
                position=pos + 1,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                cost=round(cost, 2),
                revenue=round(revenue, 2),
                device=device,
                geo=geo
            ))
        
        return results
