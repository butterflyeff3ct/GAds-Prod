"""
Google Ads Geo Targeting Service
Provides location targeting capabilities

Uses GeoTargetConstantService for location search and hierarchy
"""

import streamlit as st
from typing import List, Dict, Optional
import logging

logger = logging.getLogger('google_ads_geo')


class GoogleAdsGeoService:
    """
    Handles geo targeting operations
    Search locations, get location IDs, location hierarchy
    """
    
    def __init__(self, client):
        """
        Initialize geo targeting service
        
        Args:
            client: GoogleAdsClient instance
        """
        self.client = client
        self.geo_service = client.get_service("GeoTargetConstantService")
        self.google_ads_service = client.get_service("GoogleAdsService")
    
    def search_locations(
        self,
        query: str,
        country_code: Optional[str] = None,
        location_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for locations by name
        
        Args:
            query: Location name to search (e.g., "New York", "California")
            country_code: Limit to specific country (e.g., "US")
            location_types: Filter by type (e.g., ["City", "Region"])
            
        Returns:
            List of location dictionaries with id, name, country, type
        """
        try:
            # Build search query
            search_request = self.client.get_type("SuggestGeoTargetConstantsRequest")
            search_request.locale = "en"
            search_request.country_code = country_code or "US"
            
            # Set location names
            search_request.location_names.names.append(query)
            
            # Execute search
            response = self.geo_service.suggest_geo_target_constants(
                request=search_request
            )
            
            # Parse results
            locations = []
            for suggestion in response.geo_target_constant_suggestions:
                geo = suggestion.geo_target_constant
                
                # Filter by type if specified
                if location_types and geo.target_type not in location_types:
                    continue
                
                locations.append({
                    'id': geo.id,
                    'name': geo.name,
                    'canonical_name': geo.canonical_name,
                    'country_code': geo.country_code,
                    'target_type': geo.target_type,
                    'status': geo.status.name,
                    'resource_name': geo.resource_name
                })
            
            return locations
            
        except Exception as e:
            logger.error(f"Location search failed: {e}")
            return []
    
    def get_location_by_id(self, location_id: str) -> Optional[Dict]:
        """
        Get location details by ID
        
        Args:
            location_id: Geo target constant ID
            
        Returns:
            Dictionary with location details or None
        """
        try:
            resource_name = self.google_ads_service.geo_target_constant_path(location_id)
            
            query = f"""
                SELECT
                    geo_target_constant.id,
                    geo_target_constant.name,
                    geo_target_constant.canonical_name,
                    geo_target_constant.country_code,
                    geo_target_constant.target_type,
                    geo_target_constant.status
                FROM geo_target_constant
                WHERE geo_target_constant.resource_name = '{resource_name}'
            """
            
            response = self.google_ads_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            for row in response:
                geo = row.geo_target_constant
                return {
                    'id': geo.id,
                    'name': geo.name,
                    'canonical_name': geo.canonical_name,
                    'country_code': geo.country_code,
                    'target_type': geo.target_type,
                    'status': geo.status.name
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Location lookup failed: {e}")
            return None
    
    def get_popular_locations(self, country_code: str = "US") -> List[Dict]:
        """
        Get commonly used locations for quick selection
        
        Args:
            country_code: Country code (default: US)
            
        Returns:
            List of popular location dictionaries
        """
        # Predefined popular locations
        popular_us_locations = [
            {"id": "2840", "name": "United States", "type": "Country"},
            {"id": "1023191", "name": "New York, NY", "type": "City"},
            {"id": "1023768", "name": "Los Angeles, CA", "type": "City"},
            {"id": "1023774", "name": "Chicago, IL", "type": "City"},
            {"id": "1014221", "name": "Texas", "type": "State"},
            {"id": "21137", "name": "California", "type": "State"},
            {"id": "1023511", "name": "Florida", "type": "State"},
        ]
        
        return popular_us_locations
    
    def get_location_hierarchy(self, location_id: str) -> Dict:
        """
        Get parent and child locations
        
        Args:
            location_id: Geo target constant ID
            
        Returns:
            Dictionary with parent and child locations
        """
        try:
            resource_name = self.google_ads_service.geo_target_constant_path(location_id)
            
            query = f"""
                SELECT
                    geo_target_constant.id,
                    geo_target_constant.name,
                    geo_target_constant.parent_geo_target,
                    geo_target_constant.target_type
                FROM geo_target_constant
                WHERE geo_target_constant.resource_name = '{resource_name}'
            """
            
            response = self.google_ads_service.search(
                customer_id=self.customer_id,
                query=query
            )
            
            for row in response:
                geo = row.geo_target_constant
                return {
                    'current': {
                        'id': geo.id,
                        'name': geo.name,
                        'type': geo.target_type
                    },
                    'parent': geo.parent_geo_target if geo.parent_geo_target else None
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Location hierarchy failed: {e}")
            return {}


def get_mock_locations(query: str = "") -> List[Dict]:
    """
    Generate mock location data when API unavailable
    
    Args:
        query: Search query
        
    Returns:
        List of mock location dictionaries
    """
    all_locations = [
        {"id": "2840", "name": "United States", "country_code": "US", "target_type": "Country"},
        {"id": "2124", "name": "Canada", "country_code": "CA", "target_type": "Country"},
        {"id": "2826", "name": "United Kingdom", "country_code": "GB", "target_type": "Country"},
        {"id": "1023191", "name": "New York, NY", "country_code": "US", "target_type": "City"},
        {"id": "1023768", "name": "Los Angeles, CA", "country_code": "US", "target_type": "City"},
        {"id": "1023774", "name": "Chicago, IL", "country_code": "US", "target_type": "City"},
        {"id": "1014221", "name": "Texas", "country_code": "US", "target_type": "State"},
        {"id": "21137", "name": "California", "country_code": "US", "target_type": "State"},
        {"id": "1023511", "name": "Florida", "country_code": "US", "target_type": "State"},
        {"id": "1016367", "name": "New York", "country_code": "US", "target_type": "State"},
    ]
    
    # Filter by query if provided
    if query:
        query_lower = query.lower()
        return [
            loc for loc in all_locations
            if query_lower in loc['name'].lower()
        ]
    
    return all_locations
