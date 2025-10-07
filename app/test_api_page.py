# /app/test_api_page.py
import streamlit as st
import yaml
import os
from datetime import datetime
from typing import Optional, Dict, Any

def test_google_ads_api():
    """Test Google Ads API connection and display results."""
    st.title("🔧 Google Ads API Test")
    
    # Check if Google Ads libraries are available
    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
        GOOGLE_ADS_LIBS_AVAILABLE = True
    except ImportError:
        GOOGLE_ADS_LIBS_AVAILABLE = False
        st.warning("⚠️ Google Ads API libraries not installed. This is normal for demo mode.")
        st.info("💡 The app will use mock data instead of real API calls.")
        return
    st.markdown("Test your Google Ads API connection and credentials.")
    
    # Test status tracking
    test_results = {}
    
    # Test 1: Config file
    st.subheader("📋 Config File Test")
    with st.spinner("Checking config file..."):
        try:
            config_path = "config/config.yaml"
            if not os.path.exists(config_path):
                st.error(f"❌ Config file not found: {config_path}")
                test_results['config'] = False
                return False
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'google_ads' not in config:
                st.error("❌ 'google_ads' section not found in config file")
                test_results['config'] = False
                return False
            
            google_ads_config = config['google_ads']
            required_fields = ['client_id', 'client_secret', 'developer_token', 'login_customer_id', 'refresh_token']
            missing_fields = [field for field in required_fields if field not in google_ads_config]
            
            if missing_fields:
                st.error(f"❌ Missing required fields: {missing_fields}")
                test_results['config'] = False
                return False
            
            st.success("✅ Config file is valid")
            test_results['config'] = True
            
        except Exception as e:
            st.error(f"❌ Error reading config file: {e}")
            test_results['config'] = False
            return False
    
    # Test 2: Google Ads imports (already checked above)
    st.subheader("📦 Library Import Test")
    if GOOGLE_ADS_LIBS_AVAILABLE:
        st.success("✅ Google Ads API libraries imported successfully")
        test_results['imports'] = True
    else:
        st.warning("⚠️ Google Ads API libraries not available")
        test_results['imports'] = False
        return
    
    # Test 3: Authentication
    st.subheader("🔐 Authentication Test")
    with st.spinner("Testing Google Ads API authentication..."):
        if not GOOGLE_ADS_LIBS_AVAILABLE:
            st.warning("⚠️ Cannot test authentication - Google Ads libraries not available")
            return
        try:
            from google.ads.googleads.errors import GoogleAdsException
            
            client = GoogleAdsClient.load_from_dict(google_ads_config)
            customer_id = str(google_ads_config['login_customer_id'])
            
            st.success("✅ Google Ads client created successfully")
            st.info(f"📋 Customer ID: {customer_id}")
            
            # Test API call using correct API v28 method
            service = client.get_service("GoogleAdsService")
            query = f"""
                SELECT 
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code
                FROM customer
                WHERE customer.id = {customer_id}
            """
            
            response = service.search(customer_id=customer_id, query=query)
            customer_data = next(iter(response), None)
            
            if customer_data:
                st.success("✅ API connection successful")
                
                # Display account info
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Account Name", customer_data.customer.descriptive_name)
                    st.metric("Account ID", customer_data.customer.id)
                with col2:
                    st.metric("Currency", customer_data.customer.currency_code)
            else:
                st.warning("⚠️ No customer data found")
            
            test_results['auth'] = True
            
        except Exception as e:
            if "invalid_grant" in str(e).lower():
                st.error("❌ Refresh token has expired")
                st.warning("💡 You need to regenerate your refresh token")
            elif "AUTHENTICATION_ERROR" in str(e):
                st.error("❌ Authentication failed - check your credentials")
            elif "PERMISSION_DENIED" in str(e):
                st.error("❌ Permission denied - check your customer ID and permissions")
            else:
                st.error(f"❌ Authentication error: {e}")
            test_results['auth'] = False
            return False
    
    # Test 4: Keyword Planner API
    st.subheader("🔍 Keyword Planner API Test")
    with st.spinner("Testing Keyword Planner API..."):
        try:
            service = client.get_service("KeywordPlanIdeaService")
            request = client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = customer_id
            request.language = client.get_service("GoogleAdsService").language_constant_path("1000")  # English
            request.geo_target_constants.append(
                client.get_service("GoogleAdsService").geo_target_constant_path("2840")  # United States
            )
            request.keyword_plan_network = client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
            request.keyword_seed.keywords.extend(["test keyword", "sample search"])
            
            response = service.generate_keyword_ideas(request=request)
            keyword_count = len(list(response.results))
            
            st.success(f"✅ Keyword Planner API working - Retrieved {keyword_count} keyword ideas")
            
            if keyword_count > 0:
                # Show example results
                st.subheader("📊 Example Results")
                example_data = []
                for i, idea in enumerate(response.results):
                    if i >= 5:  # Show first 5 results
                        break
                    metrics = idea.keyword_idea_metrics
                    example_data.append({
                        'Keyword': idea.text,
                        'Monthly Searches': metrics.avg_monthly_searches or 0,
                        'Competition': metrics.competition.name,
                        'Low CPC': f"${(metrics.low_top_of_page_bid_micros / 1_000_000):.2f}" if metrics.low_top_of_page_bid_micros else "N/A",
                        'High CPC': f"${(metrics.high_top_of_page_bid_micros / 1_000_000):.2f}" if metrics.high_top_of_page_bid_micros else "N/A"
                    })
                
                st.dataframe(example_data, use_container_width=True)
            
            test_results['keyword_planner'] = True
            
        except Exception as e:
            if "AUTHENTICATION_ERROR" in str(e):
                st.error("❌ Authentication failed for Keyword Planner")
            elif "PERMISSION_DENIED" in str(e):
                st.error("❌ Permission denied for Keyword Planner API")
            else:
                st.error(f"❌ Keyword Planner error: {e}")
            test_results['keyword_planner'] = False
            return False
    
    # Final results
    st.subheader("🎯 Test Summary")
    
    all_passed = all(test_results.values())
    
    if all_passed:
        st.success("🎉 ALL TESTS PASSED!")
        st.info("""
        ✅ Your Google Ads API is properly configured
        ✅ Authentication is working
        ✅ Keyword Planner API is accessible
        ✅ The simulator should work with real Google Ads data
        """)
        
        st.balloons()
        
    else:
        st.error("❌ Some tests failed")
        failed_tests = [test for test, passed in test_results.items() if not passed]
        st.warning(f"Failed tests: {', '.join(failed_tests)}")
        
        # Show setup instructions
        with st.expander("🔧 Setup Instructions", expanded=True):
            st.markdown("""
            If you're getting authentication errors, follow these steps:
            
            1. **📋 Go to Google Ads API Center:**
               https://ads.google.com/home/tools/api-center/
            
            2. **🔑 Get your credentials:**
               - Developer Token (from API Center)
               - Client ID & Client Secret (from Google Cloud Console)
               - Customer ID (your Google Ads account ID)
            
            3. **🔄 Generate a new refresh token:**
               - Use the OAuth 2.0 Playground: https://developers.google.com/oauthplayground/
               - Select "Google Ads API v16"
               - Authorize and get your refresh token
            
            4. **📝 Update config/config.yaml with your credentials**
            
            5. **🔐 Make sure your Google Cloud project has:**
               - Google Ads API enabled
               - Proper OAuth 2.0 credentials configured
            
            6. **🎯 Ensure your Google Ads account:**
               - Has API access enabled
               - Uses the correct customer ID format (no dashes)
               - Has necessary permissions for Keyword Planner
            """)
    
    return all_passed

def render_test_api_page():
    """Render the API test page."""
    st.markdown("""
    This page tests your Google Ads API connection and credentials. 
    Use this to verify everything is working before running simulations.
    """)
    
    if st.button("🚀 Run API Tests", type="primary"):
        test_google_ads_api()
    
    st.markdown("---")
    
    # Show current config status
    st.subheader("📋 Current Configuration Status")
    
    try:
        config_path = "config/config.yaml"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'google_ads' in config:
                google_ads_config = config['google_ads']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Required Fields:**")
                    required_fields = ['client_id', 'client_secret', 'developer_token', 'login_customer_id', 'refresh_token']
                    for field in required_fields:
                        if field in google_ads_config:
                            st.success(f"✅ {field}")
                        else:
                            st.error(f"❌ {field}")
                
                with col2:
                    st.write("**Current Values:**")
                    for field in required_fields:
                        if field in google_ads_config:
                            value = google_ads_config[field]
                            # Mask sensitive values
                            if 'secret' in field.lower() or 'token' in field.lower():
                                display_value = f"{value[:10]}..." if len(str(value)) > 10 else "***"
                            else:
                                display_value = str(value)
                            st.text(f"{field}: {display_value}")
            else:
                st.error("❌ No 'google_ads' section found in config")
        else:
            st.error("❌ Config file not found")
            
    except Exception as e:
        st.error(f"❌ Error reading config: {e}")
