# /features/ad_extensions.py
"""
Ad Extensions Impact Module
Models how ad extensions improve CTR and ad prominence.
"""

from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class ExtensionType(Enum):
    """Supported ad extension types."""
    SITELINK = "sitelink"
    CALLOUT = "callout"
    STRUCTURED_SNIPPET = "structured_snippet"
    CALL = "call"
    LOCATION = "location"
    PRICE = "price"
    APP = "app"
    PROMOTION = "promotion"
    IMAGE = "image"

@dataclass
class AdExtension:
    """Represents an ad extension."""
    type: ExtensionType
    content: str
    quality: float = 0.8  # 0-1, how well-written/relevant it is
    
class ExtensionImpactCalculator:
    """
    Calculate the impact of ad extensions on performance.
    
    Based on Google research:
    - Extensions can increase CTR by 10-30%
    - More extensions = better, but diminishing returns
    - Quality matters more than quantity
    """
    
    def __init__(self):
        # Base CTR uplift per extension type (when quality = 1.0)
        self.base_ctr_uplift = {
            ExtensionType.SITELINK: 0.20,  # 20% CTR increase
            ExtensionType.CALLOUT: 0.10,
            ExtensionType.STRUCTURED_SNIPPET: 0.08,
            ExtensionType.CALL: 0.15,
            ExtensionType.LOCATION: 0.12,
            ExtensionType.PRICE: 0.18,
            ExtensionType.APP: 0.10,
            ExtensionType.PROMOTION: 0.22,
            ExtensionType.IMAGE: 0.25
        }
        
        # Quality Score impact (extensions improve QS)
        self.qs_uplift = {
            ExtensionType.SITELINK: 0.3,
            ExtensionType.CALLOUT: 0.2,
            ExtensionType.STRUCTURED_SNIPPET: 0.15,
            ExtensionType.CALL: 0.25,
            ExtensionType.LOCATION: 0.20,
            ExtensionType.PRICE: 0.15,
            ExtensionType.APP: 0.15,
            ExtensionType.PROMOTION: 0.20,
            ExtensionType.IMAGE: 0.30
        }
    
    def calculate_ctr_uplift(self, extensions: List[AdExtension], 
                            base_ctr: float) -> Dict:
        """
        Calculate total CTR uplift from all extensions.
        
        Returns:
            Dictionary with breakdown of impact
        """
        if not extensions:
            return {
                'base_ctr': base_ctr,
                'final_ctr': base_ctr,
                'total_uplift_pct': 0,
                'breakdown': []
            }
        
        total_multiplier = 1.0
        breakdown = []
        
        for ext in extensions:
            # Get base uplift for this extension type
            base_uplift = self.base_ctr_uplift.get(ext.type, 0.10)
            
            # Adjust by extension quality
            quality_adjusted_uplift = base_uplift * ext.quality
            
            # Apply to multiplier
            ext_multiplier = 1.0 + quality_adjusted_uplift
            total_multiplier *= ext_multiplier
            
            breakdown.append({
                'type': ext.type.value,
                'quality': ext.quality,
                'uplift_pct': round(quality_adjusted_uplift * 100, 1)
            })
        
        # Diminishing returns for many extensions
        if len(extensions) > 4:
            # Cap total uplift at 50%
            total_multiplier = min(total_multiplier, 1.5)
        
        final_ctr = base_ctr * total_multiplier
        total_uplift_pct = (total_multiplier - 1.0) * 100
        
        return {
            'base_ctr': round(base_ctr * 100, 2),
            'final_ctr': round(final_ctr * 100, 2),
            'total_uplift_pct': round(total_uplift_pct, 1),
            'total_multiplier': round(total_multiplier, 3),
            'extension_count': len(extensions),
            'breakdown': breakdown
        }
    
    def calculate_quality_score_boost(self, extensions: List[AdExtension],
                                     base_qs: float) -> float:
        """
        Calculate Quality Score improvement from extensions.
        
        Extensions improve expected CTR component of QS.
        """
        if not extensions:
            return base_qs
        
        total_qs_boost = 0.0
        
        for ext in extensions:
            base_boost = self.qs_uplift.get(ext.type, 0.15)
            quality_adjusted_boost = base_boost * ext.quality
            total_qs_boost += quality_adjusted_boost
        
        # QS boost is capped
        max_boost = 2.0
        total_qs_boost = min(total_qs_boost, max_boost)
        
        new_qs = base_qs + total_qs_boost
        
        return max(1.0, min(10.0, new_qs))
    
    def get_extension_recommendations(self, current_extensions: List[AdExtension],
                                     campaign_type: str = "search") -> List[str]:
        """
        Recommend which extensions to add for better performance.
        
        Args:
            current_extensions: Extensions already in use
            campaign_type: Type of campaign
        
        Returns:
            List of recommendations
        """
        current_types = {ext.type for ext in current_extensions}
        recommendations = []
        
        # Priority extensions for search campaigns
        priority_extensions = [
            (ExtensionType.SITELINK, "Add sitelinks to give users more options (+20% CTR)"),
            (ExtensionType.CALLOUT, "Add callouts to highlight key features (+10% CTR)"),
            (ExtensionType.STRUCTURED_SNIPPET, "Add structured snippets for product categories (+8% CTR)"),
            (ExtensionType.CALL, "Add call extension for phone leads (+15% CTR)"),
            (ExtensionType.PRICE, "Add price extension to show pricing (+18% CTR)"),
            (ExtensionType.PROMOTION, "Add promotion extension for sales (+22% CTR)")
        ]
        
        # Recommend missing high-value extensions
        for ext_type, recommendation in priority_extensions:
            if ext_type not in current_types:
                recommendations.append(f"➕ {recommendation}")
        
        # Quality improvement suggestions
        for ext in current_extensions:
            if ext.quality < 0.6:
                recommendations.append(
                    f"⚠️ Improve {ext.type.value} quality (currently {ext.quality*100:.0f}%)"
                )
        
        # General tips
        if len(current_extensions) < 3:
            recommendations.append("\n💡 Add at least 3 extensions for maximum impact")
        
        if not recommendations:
            recommendations.append("✅ Extension setup looks good!")
        
        return recommendations
    
    def create_sample_extensions(self, business_type: str = "ecommerce") -> List[AdExtension]:
        """
        Create sample extensions for testing/education.
        
        Args:
            business_type: Type of business (ecommerce, local, services, etc.)
        
        Returns:
            List of sample extensions
        """
        if business_type == "ecommerce":
            return [
                AdExtension(ExtensionType.SITELINK, "Shop New Arrivals", quality=0.9),
                AdExtension(ExtensionType.SITELINK, "Sale Items", quality=0.85),
                AdExtension(ExtensionType.SITELINK, "Customer Reviews", quality=0.8),
                AdExtension(ExtensionType.CALLOUT, "Free Shipping", quality=0.95),
                AdExtension(ExtensionType.CALLOUT, "30-Day Returns", quality=0.90),
                AdExtension(ExtensionType.PRICE, "$19.99 - $149.99", quality=0.85),
                AdExtension(ExtensionType.PROMOTION, "20% Off First Order", quality=0.90)
            ]
        elif business_type == "local":
            return [
                AdExtension(ExtensionType.LOCATION, "123 Main St", quality=0.95),
                AdExtension(ExtensionType.CALL, "(555) 123-4567", quality=0.90),
                AdExtension(ExtensionType.SITELINK, "Directions", quality=0.85),
                AdExtension(ExtensionType.CALLOUT, "Open 7 Days", quality=0.90)
            ]
        else:  # services
            return [
                AdExtension(ExtensionType.SITELINK, "Free Consultation", quality=0.90),
                AdExtension(ExtensionType.CALL, "Call Now", quality=0.95),
                AdExtension(ExtensionType.CALLOUT, "Licensed & Insured", quality=0.85),
                AdExtension(ExtensionType.STRUCTURED_SNIPPET, "Services: A, B, C", quality=0.80)
            ]
    
    def simulate_with_without_extensions(self, base_impressions: int, 
                                        base_ctr: float,
                                        extensions: List[AdExtension]) -> Dict:
        """
        Educational function: Show performance with and without extensions.
        
        Returns:
            Comparison showing impact
        """
        # Without extensions
        without = {
            'impressions': base_impressions,
            'ctr': base_ctr,
            'clicks': int(base_impressions * base_ctr),
            'extensions': 0
        }
        
        # With extensions
        impact = self.calculate_ctr_uplift(extensions, base_ctr)
        with_ext = {
            'impressions': base_impressions,
            'ctr': impact['final_ctr'] / 100,
            'clicks': int(base_impressions * (impact['final_ctr'] / 100)),
            'extensions': len(extensions)
        }
        
        # Calculate differences
        click_increase = with_ext['clicks'] - without['clicks']
        click_increase_pct = (click_increase / without['clicks'] * 100) if without['clicks'] > 0 else 0
        
        return {
            'without_extensions': without,
            'with_extensions': with_ext,
            'click_increase': click_increase,
            'click_increase_pct': round(click_increase_pct, 1),
            'ctr_uplift': round(impact['total_uplift_pct'], 1),
            'recommendation': f"Adding {len(extensions)} extensions would increase clicks by {click_increase:,} (+{click_increase_pct:.1f}%)"
        }
