# main.py
import streamlit as st
import os
from app.state import initialize_session_state
from app.navigation import render_sidebar, display_page
import streamlit.components.v1 as components

# Test mode detection
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
if TEST_MODE:
    try:
        from test_config import get_test_config, get_test_port
        test_config = get_test_config()
        print(f"🧪 Running in TEST MODE - Port: {get_test_port()}")
    except ImportError:
        TEST_MODE = False
        print("⚠️ Test config not found, running in normal mode")

# Disable cache clearing popup and override functions
def disabled_cache_clear(*args, **kwargs):
    """Cache clearing has been disabled to prevent popup"""
    pass

# Override cache clear methods to prevent popup
if hasattr(st, 'cache_data'):
    st.cache_data.clear = disabled_cache_clear
if hasattr(st, 'cache_resource'):  
    st.cache_resource.clear = disabled_cache_clear

# --- Page Configuration ---
if TEST_MODE:
    page_title = "Google Ads Simulator - TEST MODE"
    page_icon = "🧪"
else:
    page_title = "Google Ads Simulator"
    page_icon = "📊"

st.set_page_config(
    layout="wide",
    page_title=page_title,
    page_icon=page_icon
)

components.html("""
<script>
// Completely disable cache clearing popup and functionality
document.addEventListener('keydown', function(event) {
    // Block 'C' key to prevent cache clearing dialog
    if (event.key === 'c' || event.key === 'C') {
        event.preventDefault();
        event.stopPropagation();
        return false;
    }
}, true);

// Override the cache clearing dialog function
window.addEventListener('load', function() {
    // Find and disable any cache clearing dialogs
    const observer = new MutationObserver(() => {
        // Remove any cache clearing dialogs or modals
        const dialogs = document.querySelectorAll('[role="dialog"], .stModal, [data-testid*="modal"]');
        dialogs.forEach(dialog => {
            if (dialog.textContent && dialog.textContent.includes('Clear cache')) {
                dialog.remove();
            }
        });
        
        // Remove cache clearing menu items
        const menuItems = document.querySelectorAll('li, button, [role="menuitem"]');
        menuItems.forEach(item => {
            if (item.textContent && item.textContent.includes('Clear cache')) {
                item.style.display = 'none';
            }
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
});

// Override Streamlit's cache clearing functions
if (window.streamlit) {
    const originalCacheClear = window.streamlit.cache_data?.clear;
    if (originalCacheClear) {
        window.streamlit.cache_data.clear = function() {
            console.log('Cache clearing disabled');
            return;
        };
    }
}
</script>
""", height=0)

# --- Main Application Logic ---
def main():
    # Initialize session state on first run
    initialize_session_state()

    # Show test mode indicator
    if TEST_MODE:
        st.warning("🧪 **TEST MODE ACTIVE** - This is a test version for development and educational purposes only.")

    # Render the sidebar and get the current page selection
    page = render_sidebar()

    # Display the selected page
    display_page(page)
    
    # Render fallback chatbot if Dialogflow not configured
    if not st.secrets.get("dialogflow", {}).get("project_id"):
        render_fallback_chatbot()

def render_fallback_chatbot():
    """Render a simple fallback chatbot in bottom-right corner"""
    import streamlit.components.v1 as components
    
    chatbot_html = """
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <div id="fallback-chat" style="
            width: 320px;
            height: 400px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            border: 1px solid #ddd;
            display: none;
        ">
            <div style="background: #4285f4; color: white; padding: 12px; border-radius: 8px 8px 0 0;">
                <h4 style="margin: 0; font-size: 16px;">🤖 AI Assistant</h4>
                <p style="margin: 0; font-size: 12px; opacity: 0.9;">Google Ads Helper</p>
            </div>
            <div id="chat-content" style="height: 300px; overflow-y: auto; padding: 12px; background: #f8f9fa;">
                <div style="color: #666; font-size: 14px; margin-bottom: 12px;">
                    Hi! I can help you with Google Ads campaigns, keywords, and optimization.
                </div>
            </div>
            <div style="padding: 12px; border-top: 1px solid #ddd;">
                <input type="text" id="chat-input" placeholder="Ask about Google Ads..." style="
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 8px;
                ">
                <div style="display: flex; gap: 8px;">
                    <button onclick="sendMessage()" style="
                        background: #4285f4;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                        flex: 1;
                    ">Send</button>
                    <button onclick="toggleChat()" style="
                        background: #ccc;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Close</button>
                </div>
            </div>
        </div>
        
        <button onclick="toggleChat()" style="
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #4285f4;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 24px;
            box-shadow: 0 4px 16px rgba(66, 133, 244, 0.4);
            display: block;
        ">🤖</button>
    </div>
    
    <script>
    function toggleChat() {
        const chat = document.getElementById('fallback-chat');
        if (chat.style.display === 'none') {
            chat.style.display = 'block';
        } else {
            chat.style.display = 'none';
        }
    }
    
    function sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (message) {
            const content = document.getElementById('chat-content');
            content.innerHTML += '<div style="background: #e3f2fd; padding: 8px; margin: 8px 0; border-radius: 4px; font-size: 14px;"><strong>You:</strong> ' + message + '</div>';
            
            let response = "Thanks for your question! For detailed help, explore the Campaign Wizard or check the dashboard for insights.";
            if (message.toLowerCase().includes('campaign')) {
                response = "To create a campaign, go to the Campaign Wizard and follow the step-by-step process.";
            } else if (message.toLowerCase().includes('keyword')) {
                response = "Use the Keyword Planner to research relevant keywords for your business.";
            } else if (message.toLowerCase().includes('budget')) {
                response = "Set your daily budget in the Campaign Wizard and monitor performance in the dashboard.";
            } else if (message.toLowerCase().includes('dashboard')) {
                response = "The dashboard shows your campaign performance including clicks, impressions, and cost.";
            }
            
            content.innerHTML += '<div style="background: white; padding: 8px; margin: 8px 0; border-radius: 4px; font-size: 14px; border-left: 3px solid #34a853;"><strong>Assistant:</strong> ' + response + '</div>';
            content.scrollTop = content.scrollHeight;
            input.value = '';
        }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        const input = document.getElementById('chat-input');
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    });
    </script>
    """
    
    components.html(chatbot_html, height=0)

if __name__ == "__main__":
    main()