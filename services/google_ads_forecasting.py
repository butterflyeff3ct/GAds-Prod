"""
Google Ads Forecasting Service - FIXED
Provides keyword plan forecasting and budget simulation

Uses KeywordPlanService to generate performance predictions
"""

import streamlit as st
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('google_ads_forecasting')


class GoogleAdsForecastService:
    """
    Handles Google Ads keyword plan forecasting
    Predicts campaign performance based on keywords and budget
    """
    
    def __init__(self, client, customer_id: str):
        """
        Initialize forecasting service
        
        Args:
            client: GoogleAdsClient instance
            customer_id: Google Ads customer ID
        """
        self.client = client
        self.customer_id = customer_id
        self.keyword_plan_service = client.get_service("KeywordPlanService")
        self.keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
        self.keyword_plan_campaign_service = client.get_service("KeywordPlanCampaignService")
        self.keyword_plan_ad_group_service = client.get_service("KeywordPlanAdGroupService")
        self.keyword_plan_keyword_service = client.get_service("KeywordPlanAdGroupKeywordService")
    
    def generate_forecast(
        self,
        keywords: List[str],
        daily_budget_micros: int,
        location_ids: Optional[List[str]] = None,
        language_code: str = "1000",  # English
        network: str = "GOOGLE_SEARCH_AND_PARTNERS"
    ) -> Dict:
        """
        Generate performance forecast for keyword plan
        
        Args:
            keywords: List of keywords to forecast
            daily_budget_micros: Daily budget in micros (e.g., 100 * 1,000,000)
            location_ids: List of geo target constant IDs
            language_code: Language constant ID (default: English)
            network: Keyword plan network
            
        Returns:
            Dict with forecast metrics
        """
        try:
            # Create temporary keyword plan
            keyword_plan = self._create_keyword_plan(
                keywords=keywords,
                daily_budget_micros=daily_budget_micros,
                location_ids=location_ids or ["2840"],  # Default: United States
                language_code=language_code,
                network=network
            )
            
            # Generate forecast metrics
            forecast_metrics = self._get_forecast_metrics(keyword_plan)
            
            # Clean up temporary plan
            self._cleanup_keyword_plan(keyword_plan)
            
            return forecast_metrics
            
        except Exception as e:
            logger.error(f"Forecast generation failed: {e}")
            raise
    
    def _create_keyword_plan(
        self,
        keywords: List[str],
        daily_budget_micros: int,
        location_ids: List[str],
        language_code: str,
        network: str
    ) -> str:
        """
        Create a temporary keyword plan for forecasting
        
        Returns:
            Resource name of created keyword plan
        """
        # Create keyword plan
        keyword_plan_operation = self.client.get_type("KeywordPlanOperation")
        keyword_plan = keyword_plan_operation.create
        
        keyword_plan.name = f"Forecast Plan {datetime.now().strftime('%Y%m%d%H%M%S')}"
        keyword_plan.forecast_period.date_interval = (
            self.client.enums.KeywordPlanForecastIntervalEnum.NEXT_MONTH
        )
        
        # Create keyword plan
        keyword_plan_response = self.keyword_plan_service.mutate_keyword_plans(
            customer_id=self.customer_id,
            operations=[keyword_plan_operation]
        )
        keyword_plan_resource = keyword_plan_response.results[0].resource_name
        
        # Create campaign for keyword plan
        campaign_resource = self._create_keyword_plan_campaign(
            keyword_plan_resource,
            location_ids,
            language_code,
            network
        )
        
        # Create ad group for campaign
        ad_group_resource = self._create_keyword_plan_ad_group(
            campaign_resource
        )
        
        # Add keywords to ad group
        self._add_keywords_to_plan(
            ad_group_resource,
            keywords,
            daily_budget_micros
        )
        
        return keyword_plan_resource
    
    def _create_keyword_plan_campaign(
        self,
        keyword_plan: str,
        location_ids: List[str],
        language_code: str,
        network: str
    ) -> str:
        """Create campaign for keyword plan"""
        
        operation = self.client.get_type("KeywordPlanCampaignOperation")
        campaign = operation.create
        
        campaign.name = "Forecast Campaign"
        campaign.keyword_plan = keyword_plan
        campaign.keyword_plan_network = getattr(
            self.client.enums.KeywordPlanNetworkEnum,
            network
        )
        
        # FIXED: Set geo targets correctly
        # Create GeoTarget objects and assign them
        for location_id in location_ids:
            geo_target = self.client.get_type("KeywordPlanGeoTarget")
            geo_target.geo_target_constant = self.client.get_service(
                "GoogleAdsService"
            ).geo_target_constant_path(location_id)
            campaign.geo_targets.append(geo_target)
        
        # FIXED: Set language correctly
        # Use append instead of add
        language_path = self.client.get_service("GoogleAdsService").language_constant_path(language_code)
        campaign.language_constants.append(language_path)
        
        # Create campaign
        response = self.keyword_plan_campaign_service.mutate_keyword_plan_campaigns(
            customer_id=self.customer_id,
            operations=[operation]
        )
        
        return response.results[0].resource_name
    
    def _create_keyword_plan_ad_group(self, campaign: str) -> str:
        """Create ad group for keyword plan"""
        
        operation = self.client.get_type("KeywordPlanAdGroupOperation")
        ad_group = operation.create
        
        ad_group.name = "Forecast Ad Group"
        ad_group.keyword_plan_campaign = campaign
        ad_group.cpc_bid_micros = 1000000  # $1.00 default CPC
        
        response = self.keyword_plan_ad_group_service.mutate_keyword_plan_ad_groups(
            customer_id=self.customer_id,
            operations=[operation]
        )
        
        return response.results[0].resource_name
    
    def _add_keywords_to_plan(
        self,
        ad_group: str,
        keywords: List[str],
        daily_budget_micros: int
    ):
        """Add keywords to keyword plan ad group"""
        
        operations = []
        
        for keyword in keywords[:50]:  # Limit to 50 keywords
            operation = self.client.get_type("KeywordPlanAdGroupKeywordOperation")
            kw = operation.create
            
            kw.text = keyword
            kw.keyword_plan_ad_group = ad_group
            kw.match_type = self.client.enums.KeywordMatchTypeEnum.BROAD
            
            operations.append(operation)
        
        if operations:
            self.keyword_plan_keyword_service.mutate_keyword_plan_ad_group_keywords(
                customer_id=self.customer_id,
                operations=operations
            )
    
    def _get_forecast_metrics(self, keyword_plan: str) -> Dict:
        """
        Generate and retrieve forecast metrics for keyword plan
        
        Returns:
            Dictionary with forecast data
        """
        # Generate forecast
        response = self.keyword_plan_service.generate_forecast_metrics(
            keyword_plan=keyword_plan
        )
        
        # Extract metrics
        metrics = response.campaign_forecast_metrics
        
        return {
            'impressions': metrics.impressions or 0,
            'clicks': metrics.clicks or 0,
            'cost_micros': metrics.cost_micros or 0,
            'cost': (metrics.cost_micros or 0) / 1_000_000,
            'ctr': (metrics.clicks / metrics.impressions * 100) if metrics.impressions else 0,
            'average_cpc_micros': metrics.average_cpc or 0,
            'average_cpc': (metrics.average_cpc or 0) / 1_000_000,
            'conversions': getattr(metrics, 'conversions', 0),
            'conversion_rate': getattr(metrics, 'conversion_rate', 0),
            'cost_per_conversion_micros': getattr(metrics, 'cost_per_conversion', 0),
            'cost_per_conversion': (getattr(metrics, 'cost_per_conversion', 0)) / 1_000_000,
            'forecast_period': 'Next 30 days'
        }
    
    def _cleanup_keyword_plan(self, keyword_plan: str):
        """Delete temporary keyword plan"""
        try:
            operation = self.client.get_type("KeywordPlanOperation")
            operation.remove = keyword_plan
            
            self.keyword_plan_service.mutate_keyword_plans(
                customer_id=self.customer_id,
                operations=[operation]
            )
        except Exception as e:
            logger.warning(f"Failed to cleanup keyword plan: {e}")


def generate_mock_forecast(
    keywords: List[str],
    daily_budget: float,
    location_name: str = "United States"
) -> Dict:
    """
    Generate realistic mock forecast data when API unavailable
    
    Args:
        keywords: List of keywords
        daily_budget: Daily budget in dollars
        location_name: Target location name
        
    Returns:
        Dictionary with mock forecast metrics
    """
    import random
    
    # Calculate realistic estimates based on budget and keywords
    num_keywords = len(keywords)
    
    # Estimate impressions (higher budget = more impressions)
    base_impressions = daily_budget * random.uniform(80, 120)
    impressions = int(base_impressions * num_keywords * random.uniform(0.8, 1.2))
    
    # Estimate CTR (2-5% is typical for search)
    ctr = random.uniform(2.0, 5.0)
    clicks = int(impressions * (ctr / 100))
    
    # Calculate cost (should be near budget)
    cost = daily_budget * random.uniform(0.85, 0.95)  # Usually spend ~90% of budget
    
    # Calculate average CPC
    average_cpc = cost / clicks if clicks > 0 else daily_budget * 0.02
    
    # Estimate conversions (2-8% conversion rate typical)
    conversion_rate = random.uniform(2.0, 8.0)
    conversions = int(clicks * (conversion_rate / 100))
    
    # Cost per conversion
    cost_per_conversion = cost / conversions if conversions > 0 else cost
    
    return {
        'impressions': impressions,
        'clicks': clicks,
        'cost_micros': int(cost * 1_000_000),
        'cost': round(cost, 2),
        'ctr': round(ctr, 2),
        'average_cpc_micros': int(average_cpc * 1_000_000),
        'average_cpc': round(average_cpc, 2),
        'conversions': conversions,
        'conversion_rate': round(conversion_rate, 2),
        'cost_per_conversion_micros': int(cost_per_conversion * 1_000_000),
        'cost_per_conversion': round(cost_per_conversion, 2),
        'forecast_period': 'Next 30 days (Mock Data)',
        'is_mock': True
    }
