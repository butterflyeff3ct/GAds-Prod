# /services/gemini_client.py
import os
import time
from typing import List, Dict
import streamlit as st
from services.usage_manager import check_limit, record_usage

@st.cache_resource
def get_gemini_client():
    """Initializes and returns a GeminiClient instance, caching it."""
    api_key = st.secrets.get("gemini", {}).get("api_key")
    return GeminiClient(api_key=api_key)

class GeminiClient:
    """
    A client to interact with the Gemini API for generating keywords and ad copy.
    Includes graceful degradation when API quota is exceeded.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_GEMINI_API_KEY")
        self.use_real_api = False
        self.quota_exceeded = False
        
        if self.api_key and self.api_key != "mock":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                
                # Test the connection
                try:
                    test_response = self.model.generate_content("Test")
                    self.use_real_api = True
                    print("✅ Gemini API initialized successfully")
                except Exception as test_error:
                    if "429" in str(test_error) or "quota" in str(test_error).lower():
                        self.quota_exceeded = True
                        print("⚠️ Gemini API quota exceeded. Using mock data.")
                    else:
                        print(f"⚠️ Gemini API test failed: {test_error}")
                    self.use_real_api = False
                    
            except ImportError:
                print("⚠️ google-generativeai not installed. Using mock data.")
                self.use_real_api = False
            except Exception as e:
                print(f"⚠️ Gemini initialization error: {e}")
                self.use_real_api = False
        else:
            print("ℹ️ No Gemini API key. Using mock data for AI features.")
    
    def _handle_api_error(self, error: Exception, operation: str):
        """Centralized error handling for API calls."""
        error_str = str(error)
        
        if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
            self.quota_exceeded = True
            self.use_real_api = False  # Switch to mock mode
            st.warning(f"""
            ⚠️ **Gemini API Quota Exceeded**
            
            The free tier allows 50 requests per day. You've reached this limit.
            
            **No worries!** The simulator will continue using realistic mock data instead.
            Your campaign will work perfectly - just without AI-generated content.
            
            To use AI features again:
            - Wait 24 hours for quota reset, OR
            - Upgrade to paid tier at https://ai.google.dev/pricing
            
            *{operation} will use educational mock data.*
            """)
            return True
        else:
            st.error(f"Gemini API error during {operation}: {error}")
            return False
    
    def generate_keywords(self, prompt: str) -> List[str]:
        """Generates keywords with graceful fallback on quota exceeded."""
        # Check quota limits first
        within_limit, reason = check_limit("gemini")
        if not within_limit:
            st.warning(f"🚫 Gemini quota exceeded: {reason}")
            st.info("💡 Using mock keywords (quota exceeded)")
            return self._generate_mock_keywords(prompt)
        
        if self.quota_exceeded:
            st.info("💡 Using mock keywords (API quota exceeded)")
            return self._generate_mock_keywords(prompt)
        
        if self.use_real_api:
            try:
                full_prompt = f"""
                Act as a Google Ads specialist. Based on the product description, generate 20 relevant keywords.
                
                Product: "{prompt}"
                
                Include:
                - 5 high-intent commercial keywords
                - 5 long-tail keywords (3-5 words)
                - 5 informational keywords
                - 5 competitor/comparison keywords
                
                Return ONLY comma-separated keywords, no formatting.
                """
                
                response = self.model.generate_content(full_prompt)
                
                # Record token usage
                tokens_used = len(full_prompt) + len(response.text) if response.text else len(full_prompt)
                record_usage("gemini", tokens_used)
                
                # Log detailed usage for monitoring
                try:
                    from monitor.gemini_monitor import log_gemini_generation
                    import time
                    start_time = time.time()
                    response_time = int((time.time() - start_time) * 1000)
                    
                    # Extract actual token usage from response if available
                    actual_tokens = tokens_used
                    if hasattr(response, 'usage_metadata') and response.usage_metadata:
                        actual_tokens = getattr(response.usage_metadata, 'total_token_count', tokens_used)
                    
                    log_gemini_generation("generate_keywords", actual_tokens, response_time, True)
                except ImportError:
                    pass  # Monitor not available
                
                keywords = response.text.strip().split(",")
                return [kw.strip() for kw in keywords if kw.strip()]
                
            except Exception as e:
                if self._handle_api_error(e, "Keyword generation"):
                    return self._generate_mock_keywords(prompt)
                raise
        else:
            return self._generate_mock_keywords(prompt)
    
    def generate_ads(self, prompt: str, num_headlines: int, num_descriptions: int, tone: str) -> Dict[str, List[str]]:
        """Generates ad copy with graceful fallback."""
        # Check quota limits first
        within_limit, reason = check_limit("gemini")
        if not within_limit:
            st.warning(f"🚫 Gemini quota exceeded: {reason}")
            st.info("💡 Using mock ad copy (quota exceeded)")
            return self._generate_mock_ads(prompt, num_headlines, num_descriptions)
        
        if self.quota_exceeded:
            st.info("💡 Using mock ad copy (API quota exceeded)")
            return self._generate_mock_ads(prompt, num_headlines, num_descriptions)
        
        if self.use_real_api:
            try:
                full_prompt = f"""
                Create Google Ads copy with {tone} tone.
                
                Product: "{prompt}"

                Generate:
                - {num_headlines} headlines (max 30 chars each)
                - {num_descriptions} descriptions (max 90 chars each)

                Format as:
                H: [headline]
                D: [description]
                """
                
                response = self.model.generate_content(full_prompt)
                
                # Record token usage
                tokens_used = len(full_prompt) + len(response.text) if response.text else len(full_prompt)
                record_usage("gemini", tokens_used)
                
                return self._parse_ad_response(response.text)
                
            except Exception as e:
                if self._handle_api_error(e, "Ad generation"):
                    return self._generate_mock_ads(prompt, num_headlines, num_descriptions)
                raise
        else:
            return self._generate_mock_ads(prompt, num_headlines, num_descriptions)
    
    def generate_campaign_insights(self, campaign_config: Dict) -> str:
        """Generates insights with graceful fallback."""
        # Check quota limits first
        within_limit, reason = check_limit("gemini")
        if not within_limit:
            st.warning(f"🚫 Gemini quota exceeded: {reason}")
            st.info("💡 Using mock insights (quota exceeded)")
            return self._generate_mock_insights(campaign_config)
        
        if self.quota_exceeded:
            st.info("💡 Using mock insights (API quota exceeded)")
            return self._generate_mock_insights(campaign_config)
        
        if self.use_real_api:
            try:
                full_prompt = f"""
                Analyze this Google Ads campaign:
                
                - Objective: {campaign_config.get('objective')}
                - Budget: ${campaign_config.get('daily_budget', 0)}/day
                - Bidding: {campaign_config.get('bidding_strategy')}
                - Ad Groups: {len(campaign_config.get('ad_groups', []))}
                
                Provide:
                1. Performance predictions
                2. Optimization tips
                3. Risk assessment
                4. Next steps
                """
                
                response = self.model.generate_content(full_prompt)
                
                # Record token usage
                tokens_used = len(full_prompt) + len(response.text) if response.text else len(full_prompt)
                record_usage("gemini", tokens_used)
                
                return response.text
                
            except Exception as e:
                if self._handle_api_error(e, "Campaign insights"):
                    return self._generate_mock_insights(campaign_config)
                raise
        else:
            return self._generate_mock_insights(campaign_config)
    
    def _parse_ad_response(self, text: str) -> Dict[str, List[str]]:
        """Parses API response."""
        lines = text.strip().split("\n")
        result = {"headlines": [], "descriptions": []}
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith("H:"):
                result["headlines"].append(line[2:].strip())
            elif line.upper().startswith("D:"):
                result["descriptions"].append(line[2:].strip())
        
        return result
    
    def _generate_mock_keywords(self, prompt: str) -> List[str]:
        """Generates realistic mock keywords."""
        # Detect product type
        base = "product"
        prompt_lower = prompt.lower()
        
        if "battery" in prompt_lower or "power" in prompt_lower:
            base = "battery pack"
        elif "shoe" in prompt_lower or "footwear" in prompt_lower:
            base = "running shoes"
        elif "laptop" in prompt_lower or "computer" in prompt_lower:
            base = "laptop"
        elif "phone" in prompt_lower or "smartphone" in prompt_lower:
            base = "smartphone"
        
        return [
            # Commercial intent
            f"buy {base}",
            f"{base} for sale",
            f"best {base} 2025",
            f"cheap {base}",
            f"{base} deals",
            # Long-tail
            f"high quality {base} with warranty",
            f"durable {base} for professionals",
            f"lightweight {base} for travel",
            f"affordable {base} online",
            f"premium {base} free shipping",
            # Informational
            f"how to choose {base}",
            f"what is the best {base}",
            f"{base} buying guide",
            f"{base} reviews 2025",
            f"{base} comparison",
            # Competitor/Comparison
            f"{base} vs alternatives",
            f"compare {base} brands",
            f"is {base} worth it",
            f"top rated {base}",
            f"{base} alternatives"
        ]
    
    def _generate_mock_ads(self, prompt: str, num_headlines: int, num_descriptions: int) -> Dict[str, List[str]]:
        """Generates realistic mock ad copy."""
        product = "Product"
        if "battery" in prompt.lower():
            product = "Power Solution"
        elif "shoe" in prompt.lower():
            product = "Athletic Footwear"
        
        headlines = [
            f"Premium {product} Sale",
            "Free Shipping Today",
            "2-Year Warranty Included",
            "Top Rated by Experts",
            "Shop The Collection",
            "Limited Time Offer",
            "Best Price Guaranteed",
            "Order Now & Save"
        ]
        
        descriptions = [
            f"Discover our range of high-quality {product}s. Fast, free shipping on all orders.",
            f"Unbeatable prices on premium {product}s. Click to see deals and save today.",
            f"Engineered for performance. All products come with warranty and support."
        ]
        
        return {
            "headlines": headlines[:num_headlines],
            "descriptions": descriptions[:num_descriptions]
        }
    
    def _generate_mock_insights(self, campaign_config: Dict) -> str:
        """Generates realistic mock campaign insights."""
        objective = campaign_config.get('objective', 'Sales')
        budget = campaign_config.get('daily_budget', 100)
        
        return f"""
## 🤖 Campaign Analysis (Educational Mock Data)

### 📊 Performance Predictions
- **Expected CTR**: 2.5-4.2% (Above average for {objective})
- **Estimated CPC**: ${budget * 0.15:.2f} - ${budget * 0.25:.2f}
- **Conversion Rate**: 3.8-6.2%
- **Monthly Conversions**: {int(budget * 0.5)}-{int(budget * 0.8)}

### 🎯 Optimization Recommendations
1. **Keywords**: Focus on long-tail for better Quality Scores
2. **Ad Copy**: Test 5+ headlines with emotional triggers
3. **Landing Pages**: Ensure mobile optimization (70%+ traffic)
4. **Bidding**: Target CPA recommended for conversion optimization

### 🧠 AI Features Available
- Smart Bidding for real-time optimization
- Audience Expansion to find similar users
- Automated ad testing
- Budget optimization across keywords

### ⚠️ Risk Assessment
- **Campaign Structure**: ✅ Solid
- **Budget Level**: ⚠️ May limit competitive keywords
- **Mitigation**: Start broad, refine based on data

### 🚀 Next Steps
1. Launch with 3-5 ad groups
2. Monitor for 7 days before major changes
3. Enable conversion tracking
4. Set up automated rules

*Note: This is educational mock data. Real AI insights available when API quota resets.*
        """
