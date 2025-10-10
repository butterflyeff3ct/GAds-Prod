"""
Example of how to integrate session tracking into existing services.
This shows how to modify services to automatically track API calls and operations.
"""

# Example 1: Modified Gemini Client with session tracking
class GeminiClientWithTracking:
    """Example of Gemini client with automatic session tracking"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # ... existing initialization code ...
    
    def generate_content(self, prompt: str, **kwargs):
        """Generate content with automatic token tracking"""
        from utils.session_helpers import track_gemini_call
        
        try:
            # Make the actual API call
            response = self._make_gemini_call(prompt, **kwargs)
            
            # Track the operation and tokens used
            if hasattr(response, 'usage_metadata'):
                tokens_used = response.usage_metadata.total_token_count
                track_gemini_call(tokens_used)
            else:
                # Estimate tokens if not available
                estimated_tokens = len(prompt.split()) * 1.3  # Rough estimate
                track_gemini_call(int(estimated_tokens))
            
            return response
            
        except Exception as e:
            # Track error
            from utils.session_helpers import track_api_call
            track_api_call("gemini_error", 0)
            raise e


# Example 2: Google Ads Client with tracking
class GoogleAdsClientWithTracking:
    """Example of Google Ads client with automatic operation tracking"""
    
    def create_campaign(self, campaign_data):
        """Create campaign with operation tracking"""
        from utils.session_helpers import track_campaign_creation
        
        try:
            # Track the operation
            track_campaign_creation()
            
            # Make the actual API call
            result = self._make_ads_api_call("create_campaign", campaign_data)
            
            return result
            
        except Exception as e:
            # Track error
            from utils.session_helpers import track_api_call
            track_api_call("campaign_creation_error", 0)
            raise e


# Example 3: Using decorators for automatic tracking
from utils.session_helpers import track_operation

class SimulationService:
    """Example service using decorators for automatic tracking"""
    
    @track_operation("simulation_run", 0)
    def run_simulation(self, parameters):
        """Run simulation with automatic tracking"""
        # Your simulation logic here
        return simulation_results
    
    @track_operation("keyword_research", 50)  # Estimate 50 tokens per research
    def research_keywords(self, query):
        """Research keywords with token tracking"""
        # Your keyword research logic here
        return keywords


# Example 4: Manual tracking in existing functions
def existing_function_with_tracking():
    """Example of adding tracking to existing functions"""
    from utils.session_helpers import track_api_call
    
    # Track the start of operation
    track_api_call("complex_analysis", 0)
    
    try:
        # Your existing logic here
        result = perform_complex_analysis()
        
        # Track successful completion with estimated tokens
        track_api_call("complex_analysis_complete", 100)
        
        return result
        
    except Exception as e:
        # Track error
        track_api_call("complex_analysis_error", 0)
        raise e


# Example 5: Page-level session statistics
def show_page_with_session_stats():
    """Example of showing session stats on a page"""
    import streamlit as st
    from utils.session_helpers import show_session_stats, get_session_summary
    
    # Your page content
    st.title("Campaign Dashboard")
    
    # Show session statistics in sidebar
    show_session_stats()
    
    # Get session summary for custom display
    summary = get_session_summary()
    if summary:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Session Tokens", summary.get('tokens_used', 0))
        with col2:
            st.metric("Operations", summary.get('operations_count', 0))
        with col3:
            duration_min = summary.get('duration_ms', 0) / (1000 * 60)
            st.metric("Duration", f"{duration_min:.1f} min")


# Example 6: Integration with existing state management
def integrate_with_state_manager():
    """Example of integrating with existing state management"""
    from app.state_manager import get_state
    from utils.session_helpers import track_api_call
    
    # Get existing state
    state = get_state()
    
    # Track state changes as operations
    if state.get('campaign_created'):
        track_api_call("campaign_state_change", 0)
    
    if state.get('keywords_generated'):
        track_api_call("keywords_generated", 0)


# Example 7: Error handling with session tracking
def robust_api_call_with_tracking():
    """Example of robust API calls with comprehensive tracking"""
    from utils.session_helpers import track_api_call
    import time
    
    start_time = time.time()
    
    try:
        # Track start
        track_api_call("api_request_start", 0)
        
        # Make API call
        result = make_api_call()
        
        # Track success with timing
        duration = time.time() - start_time
        track_api_call("api_request_success", 0)
        
        return result
        
    except Exception as e:
        # Track error with timing
        duration = time.time() - start_time
        track_api_call("api_request_error", 0)
        
        # Log error details
        st.error(f"API call failed after {duration:.2f}s: {e}")
        raise e


# Example 8: Batch operation tracking
def batch_operations_with_tracking():
    """Example of tracking batch operations efficiently"""
    from utils.session_helpers import track_api_call
    
    # Track batch start
    track_api_call("batch_operations_start", 0)
    
    operations = ["op1", "op2", "op3"]
    results = []
    
    for i, operation in enumerate(operations):
        try:
            # Track individual operation
            track_api_call(f"batch_op_{i+1}", 0)
            
            result = perform_operation(operation)
            results.append(result)
            
        except Exception as e:
            # Track individual error
            track_api_call(f"batch_op_{i+1}_error", 0)
            st.error(f"Operation {i+1} failed: {e}")
    
    # Track batch completion
    track_api_call("batch_operations_complete", 0)
    
    return results

