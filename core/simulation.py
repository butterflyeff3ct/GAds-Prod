# /core/simulation.py
import pandas as pd
import streamlit as st
import hashlib
import random
from typing import Dict, List
from features.planner import get_keyword_metrics_batch, KWPSource, GOOGLE_ADS_API_AVAILABLE
from core.auction import AuctionEngine
from core.bidding import BiddingEngine, BidContext
from core.matching import MatchEngine
from core.quality import QualityEngine
from core.pacing import PacingController
from data_models.schemas import Ad, Keyword, Campaign, AdGroup, AdSchedule, Status
from features.ad_extensions import ExtensionImpactCalculator, AdExtension as ExtObj, ExtensionType

def get_deterministic_seed(config: dict) -> int:
    """
    Generate a deterministic seed from campaign configuration.
    
    Uses SHA256 hash to ensure consistent results across Python sessions,
    unlike Python's built-in hash() which is randomized per session.
    """
    campaign_name = config.get('campaign', {}).get('name', 'default')
    # Sort keywords for consistent ordering
    keywords_text = '|'.join(sorted([kw['text'] for kw in config.get('keywords', [])]))
    concat = f"{campaign_name}_{keywords_text}"
    
    # Use SHA256 for deterministic hashing
    seed = int(hashlib.sha256(concat.encode()).hexdigest(), 16) % (2**32)
    return seed

def run_simulation(config: Dict) -> pd.DataFrame:
    """
    Run a deterministic, functional simulation matching Google Ads behavior.
    
    NEW FEATURES IN THIS VERSION:
    - Keyword-level bidding (individual CPC bids)
    - Negative keywords (campaign + ad group level)
    - Device bid adjustments (actually applied)
    - Ad scheduling enforcement (dayparting)
    - Ad extensions CTR impact
    """
    
    # ========== INITIALIZATION ==========
    campaign_name = config.get('campaign', {}).get('name', 'default')
    deterministic_seed = get_deterministic_seed(config)
    
    # Seed all random number generators for deterministic results
    random.seed(deterministic_seed)
    
    st.info(f"""
    🎓 **Google Ads Search Campaign Simulator**
    - Campaign: {campaign_name}
    - Deterministic Seed: {deterministic_seed}
    - **NEW:** Keyword-level bids, Negative keywords, Device targeting, Ad scheduling
    - **FIXED:** Truly deterministic results across sessions
    """)
    
    # Extract configuration
    campaign_info = config.get('campaign', {})
    daily_budget = float(campaign_info.get('daily_budget', 100.0))
    days = config.get('simulation', {}).get('days', 7)
    industry = config.get('industry', 'default')
    
    keywords_list = config.get('keywords', [])
    ads_list = config.get('ads', [])
    ad_groups_list = config.get('ad_groups', [])
    
    # ========== FEATURE 1: NEGATIVE KEYWORDS ==========
    campaign_negatives = config.get('negative_keywords', [])
    if campaign_negatives:
        st.success(f"✅ Campaign negative keywords: {len(campaign_negatives)}")
    
    # Build ad group negative keywords map
    ag_negatives = {}
    for ag in ad_groups_list:
        ag_id = ag.get('id')
        ag_negatives[ag_id] = ag.get('negative_keywords', [])
    
    # ========== FEATURE 2: AD SCHEDULING ==========
    ad_schedule_config = campaign_info.get('ad_schedule', {'enabled': False})
    ad_schedule = AdSchedule(**ad_schedule_config)
    if ad_schedule.enabled:
        st.success("✅ Ad scheduling enabled (dayparting active)")
    
    # ========== FEATURE 3: DEVICE BID ADJUSTMENTS ==========
    device_adjustments = campaign_info.get('device_bid_adjustments', {
        'desktop': 1.0,
        'mobile': 1.0,
        'tablet': 1.0
    })
    has_device_adjustments = any(v != 1.0 for v in device_adjustments.values())
    if has_device_adjustments:
        st.success(f"✅ Device bid adjustments: Mobile {device_adjustments.get('mobile', 1.0):.0%}, Desktop {device_adjustments.get('desktop', 1.0):.0%}")
    
    # Validation
    if not keywords_list:
        st.error("❌ No keywords found.")
        return pd.DataFrame()
    
    if not ads_list:
        st.warning("⚠️ Creating default ad")
        ads_list = [{
            "id": "ad_default",
            "ad_group_id": keywords_list[0].get('ad_group_id', 'ag_1'),
            "headlines": ["Default Ad"],
            "descriptions": ["Default description"],
            "final_url": "http://example.com",
            "callouts": [],
            "sitelinks": []
        }]
    
    # ========== FETCH KEYWORD METRICS ==========
    use_real_data = st.session_state.get('use_api_data', True) and GOOGLE_ADS_API_AVAILABLE
    source = KWPSource.GOOGLE_ADS_API if use_real_data else KWPSource.MOCK
    
    st.info(f"🔍 Fetching metrics from {source.name}...")
    
    all_keywords_text = [kw['text'] for kw in keywords_list]
    keyword_metrics = get_keyword_metrics_batch(keywords=all_keywords_text, source=source)
    
    valid_count = sum(1 for m in keyword_metrics.values() if m)
    if valid_count == 0:
        st.warning("⚠️ Falling back to mock data")
        keyword_metrics = get_keyword_metrics_batch(keywords=all_keywords_text, source=KWPSource.MOCK)
    
    st.success(f"✅ Retrieved metrics for {len(keyword_metrics)} keywords")
    
    # ========== BUILD DATA STRUCTURES ==========
    keywords_by_text = {}
    ad_groups_by_id = {}
    
    # Build ad groups with default bids
    for ag_data in ad_groups_list:
        ag_id = ag_data.get('id')
        ad_groups_by_id[ag_id] = {
            'default_bid': ag_data.get('default_bid', 1.0),
            'negative_keywords': ag_data.get('negative_keywords', [])
        }
    
    # Build keywords with individual bids
    for kw in keywords_list:
        kw_obj = Keyword(**kw)
        keywords_by_text[kw['text'].lower()] = kw_obj
    
    # Build ads by ad group with extensions
    ads_by_ag = {}
    extension_calculator = ExtensionImpactCalculator()
    
    for ad_data in ads_list:
        ad = Ad(**ad_data)
        ag_id = ad.ad_group_id
        if ag_id not in ads_by_ag:
            ads_by_ag[ag_id] = []
        ads_by_ag[ag_id].append(ad)
    
    st.info(f"📊 {len(keywords_by_text)} keywords, {len(ad_groups_by_id)} ad groups, {len(ads_list)} ads")
    
    # ========== INITIALIZE ENGINES ==========
    auction_engine = AuctionEngine()
    bidding_engine = BiddingEngine(
        strategy=config.get('bidding_strategy', 'manual_cpc'),
        base_bid=1.5,
        target_cpa=config.get('target_cpa', 20.0),
        target_roas=config.get('target_roas', 4.0)
    )
    match_engine = MatchEngine()
    quality_engine = QualityEngine()
    pacing_controller = PacingController(daily_budget)
    
    # ========== RUN SIMULATION WITH NEW FEATURES ==========
    all_results = []
    progress_bar = st.progress(0, text="Starting simulation...")
    
    stats = {
        'total_queries': 0,
        'auctions_run': 0,
        'filtered_by_negatives': 0,
        'filtered_by_schedule': 0,
        'filtered_by_budget': 0,
        'device_breakdown': {'desktop': 0, 'mobile': 0, 'tablet': 0}
    }
    
    for day in range(days):
        pacing_controller.reset_daily()
        day_of_week = day % 7  # 0=Monday, 6=Sunday
        
        for hour in range(24):
            pacing_controller.update_hour(hour)
            
            # FEATURE 4: Ad Scheduling Check
            if not ad_schedule.is_active(day_of_week, hour):
                stats['filtered_by_schedule'] += 1
                continue  # Skip this hour - ads not scheduled
            
            # Simulate different devices (70% desktop, 20% mobile, 10% tablet)
            device_distribution = [
                ('desktop', 0.70),
                ('mobile', 0.20),
                ('tablet', 0.10)
            ]
            
            for kw_text, metrics in keyword_metrics.items():
                if not metrics:
                    continue
                
                hourly_searches = metrics.daily_searches / 24
                hour_mult = auction_engine.hourly_distribution[hour]
                queries_this_hour = int(hourly_searches * hour_mult * 24)
                queries_this_hour = max(1, min(queries_this_hour, 50))
                
                stats['total_queries'] += queries_this_hour
                
                # Find keyword object
                kw_text_normalized = kw_text.lower()
                if kw_text_normalized not in keywords_by_text:
                    matched = False
                    for campaign_kw in keywords_by_text.keys():
                        if campaign_kw in kw_text_normalized or kw_text_normalized in campaign_kw:
                            kw_text_normalized = campaign_kw
                            matched = True
                            break
                    if not matched:
                        continue
                
                keyword_obj = keywords_by_text[kw_text_normalized]
                
                # Skip if keyword is paused
                if keyword_obj.status != Status.ENABLED:
                    continue
                
                ads_for_keyword = ads_by_ag.get(keyword_obj.ad_group_id, [])
                if not ads_for_keyword:
                    continue
                
                # Get ad group info
                ag_info = ad_groups_by_id.get(keyword_obj.ad_group_id, {'default_bid': 1.0, 'negative_keywords': []})
                
                # Run queries for each device type
                for device, device_pct in device_distribution:
                    device_queries = int(queries_this_hour * device_pct)
                    if device_queries == 0:
                        continue
                    
                    stats['device_breakdown'][device] += device_queries
                    
                    for query_num in range(device_queries):
                        if not pacing_controller.should_participate():
                            stats['filtered_by_budget'] += 1
                            break
                        
                        query = kw_text
                        
                        # FEATURE 2: Negative Keywords Check
                        # Check campaign-level negatives
                        if match_engine.is_negative_hit(query, campaign_negatives):
                            stats['filtered_by_negatives'] += 1
                            continue
                        
                        # Check ad group-level negatives
                        if match_engine.is_negative_hit(query, ag_info['negative_keywords']):
                            stats['filtered_by_negatives'] += 1
                            continue
                        
                        # FEATURE 1: Keyword-Level Bidding
                        context = BidContext(
                            hour=hour,
                            day_of_week=day_of_week,
                            device=device,
                            quality_score=metrics.quality_score,
                            historical_ctr=metrics.expected_ctr,
                            historical_cvr=metrics.expected_cvr,
                            keyword_text=kw_text,
                            match_type=keyword_obj.match_type
                        )
                        
                        # Get keyword-specific bid or ad group default
                        keyword_bid = keyword_obj.get_bid(ag_info['default_bid'])
                        base_bid = bidding_engine.get_bid(
                            cvr_hat=metrics.expected_cvr,
                            value_hat=100.0,
                            context=context
                        )
                        
                        # Use keyword-level bid if set, otherwise use strategy bid
                        if keyword_obj.cpc_bid is not None:
                            final_bid = keyword_bid
                        else:
                            final_bid = base_bid
                        
                        # FEATURE 3: Device Bid Adjustments
                        device_adjustment = device_adjustments.get(device, 1.0)
                        final_bid *= device_adjustment
                        
                        # Apply pacing throttle
                        final_bid = pacing_controller.apply_throttle(final_bid)
                        
                        # Calculate Quality Score with extensions
                        expected_ctr = quality_engine.calculate_expected_ctr(
                            keyword=kw_text,
                            ad_headlines=ads_for_keyword[0].headlines,
                            historical_ctr=metrics.expected_ctr
                        )
                        
                        ad_text = ' '.join(ads_for_keyword[0].headlines + ads_for_keyword[0].descriptions)
                        ad_relevance = quality_engine.calculate_ad_relevance(
                            keyword=kw_text,
                            ad_text=ad_text,
                            query=query
                        )
                        
                        lp_exp = quality_engine.calculate_landing_page_experience(
                            url=ads_for_keyword[0].final_url,
                            keyword=kw_text
                        )
                        
                        base_qs = quality_engine.compute_qs(expected_ctr, ad_relevance, lp_exp)
                        
                        # FEATURE 5: Ad Extensions Impact
                        extensions = ads_for_keyword[0].get_all_extensions()
                        if extensions:
                            # Convert to extension objects for calculator
                            ext_objects = []
                            for ext in extensions:
                                try:
                                    ext_type = ExtensionType(ext.type)
                                    ext_objects.append(ExtObj(type=ext_type, content=ext.text, quality=0.8))
                                except:
                                    pass
                            
                            # Apply CTR uplift from extensions
                            if ext_objects:
                                ext_impact = extension_calculator.calculate_ctr_uplift(ext_objects, expected_ctr)
                                expected_ctr = ext_impact['final_ctr'] / 100
                                
                                # Extensions also boost QS slightly
                                qs_boost = extension_calculator.calculate_quality_score_boost(ext_objects, base_qs)
                                qs = qs_boost
                            else:
                                qs = base_qs
                        else:
                            qs = base_qs
                        
                        # Run auction
                        auction_results = auction_engine.run_auction(
                            query=query,
                            ads=ads_for_keyword,
                            bids=[final_bid],
                            qs_scores=[qs],
                            base_ctr=[expected_ctr],
                            cvr_preds=[metrics.expected_cvr],
                            hour=hour,
                            device=device,
                            geo='US',
                            revenue_per_conv=100.0,
                            industry=industry,
                            day_of_week=day_of_week
                        )
                        
                        for result in auction_results:
                            pacing_controller.record_spend(result.cost)
                            
                            result_dict = result.dict()
                            result_dict.update({
                                'day': day + 1,
                                'hour': hour,
                                'day_of_week': day_of_week,
                                'campaign': campaign_info.get('name', 'Campaign'),
                                'bidding_strategy': config.get('bidding_strategy', 'manual_cpc'),
                                'quality_score': qs,
                                'expected_ctr': expected_ctr,
                                'ad_relevance': ad_relevance,
                                'landing_page_exp': lp_exp,
                                'keyword_bid': keyword_bid,
                                'device_adjustment': device_adjustment,
                                'final_bid_used': final_bid,
                                'has_extensions': len(extensions) > 0,
                                'extension_count': len(extensions),
                                'using_real_data': use_real_data
                            })
                            
                            all_results.append(result_dict)
                            stats['auctions_run'] += 1
        
        progress_bar.progress((day + 1) / days, text=f"Day {day + 1}/{days}")
    
    # ========== STATISTICS ==========
    st.success(f"""
    ✅ **Simulation Complete!**
    - Days: {days}
    - Total queries: {stats['total_queries']:,}
    - Auctions run: {stats['auctions_run']:,}
    - Filtered by negatives: {stats['filtered_by_negatives']:,}
    - Filtered by schedule: {stats['filtered_by_schedule']:,}
    - Filtered by budget: {stats['filtered_by_budget']:,}
    """)
    
    # Device breakdown
    total_device_queries = sum(stats['device_breakdown'].values())
    if total_device_queries > 0:
        st.info(f"""
        📱 **Device Distribution:**
        - Desktop: {stats['device_breakdown']['desktop']:,} ({stats['device_breakdown']['desktop']/total_device_queries*100:.1f}%)
        - Mobile: {stats['device_breakdown']['mobile']:,} ({stats['device_breakdown']['mobile']/total_device_queries*100:.1f}%)
        - Tablet: {stats['device_breakdown']['tablet']:,} ({stats['device_breakdown']['tablet']/total_device_queries*100:.1f}%)
        """)
    
    if all_results:
        results_df = pd.DataFrame(all_results)
        
        # Add calculated metrics
        results_df['ctr'] = (results_df['clicks'] / results_df['impressions'] * 100).fillna(0)
        results_df['cvr'] = (results_df['conversions'] / results_df['clicks'] * 100).fillna(0)
        results_df['roas'] = (results_df['revenue'] / results_df['cost']).fillna(0)
        
        return results_df
    else:
        st.warning("⚠️ No results generated")
        return pd.DataFrame()
