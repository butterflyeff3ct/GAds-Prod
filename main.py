# main.py
import streamlit as st
from app.state import initialize_session_state
from app.navigation import render_sidebar, display_page
import streamlit.components.v1 as components

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
st.set_page_config(
    layout="wide",
    page_title="Google Ads Simulator",
    page_icon="📊"
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

    # Render the sidebar and get the current page selection
    page = render_sidebar()

    # Display the selected page
    display_page(page)

if __name__ == "__main__":
    main()