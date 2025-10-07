# dialogflow_messenger.py
"""
Dialogflow Messenger integration for Streamlit
Forces positioning in bottom-right corner using JavaScript injection
Prevents Streamlit keyboard shortcuts from interfering with chat input
"""

import streamlit.components.v1 as components

def render_dialogflow_chat(project_id: str, agent_id: str, location: str = "us-central1"):
    """
    Render Dialogflow Messenger in bottom-right corner using JavaScript injection
    """
    
    # JavaScript to inject Dialogflow Messenger into the parent frame
    js_code = f"""
    <script>
    (function() {{
        // Check if we're in an iframe (Streamlit component)
        const targetDoc = window.parent.document || document;
        
        // Remove any existing messenger to avoid duplicates
        const existing = targetDoc.querySelector('df-messenger');
        if (existing) {{
            existing.remove();
        }}
        
        // Inject the script if not present
        if (!targetDoc.querySelector('script[src*="df-messenger.js"]')) {{
            const script = targetDoc.createElement('script');
            script.src = 'https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js';
            script.async = true;
            targetDoc.head.appendChild(script);
            
            const link = targetDoc.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/themes/df-messenger-default.css';
            targetDoc.head.appendChild(link);
        }}
        
        // Create and inject custom styles
        const styleId = 'df-messenger-custom-styles';
        if (!targetDoc.getElementById(styleId)) {{
            const style = targetDoc.createElement('style');
            style.id = styleId;
            style.innerHTML = `
                df-messenger {{
                    position: fixed !important;
                    bottom: 20px !important;
                    right: 20px !important;
                    left: auto !important;
                    top: auto !important;
                    z-index: 999999 !important;
                }}
                
                df-messenger-chat {{
                    position: relative !important;
                }}
                
                /* When minimized - show as button */
                df-messenger-chat[minimized] {{
                    width: 56px !important;
                    height: 56px !important;
                }}
                
                /* When expanded - show chat window */
                df-messenger-chat:not([minimized]) {{
                    width: 350px !important;
                    height: 500px !important;
                    margin-bottom: 10px !important;
                }}
            `;
            targetDoc.head.appendChild(style);
        }}
        
        // Wait a moment for scripts to load, then create messenger
        setTimeout(() => {{
            const messenger = targetDoc.createElement('df-messenger');
            messenger.setAttribute('location', '{location}');
            messenger.setAttribute('project-id', '{project_id}');
            messenger.setAttribute('agent-id', '{agent_id}');
            messenger.setAttribute('language-code', 'en');
            messenger.setAttribute('chat-title', 'Google Ads Assistant');
            messenger.setAttribute('intent', 'WELCOME');
            messenger.setAttribute('expand', 'false');
            
            targetDoc.body.appendChild(messenger);
            
            // IMPORTANT: Prevent Streamlit keyboard shortcuts when typing in chat
            setTimeout(() => {{
                const chatInput = targetDoc.querySelector('df-messenger');
                if (chatInput) {{
                    // Add event listeners to prevent keyboard event propagation
                    chatInput.addEventListener('click', () => {{
                        // When chat is clicked, disable Streamlit shortcuts
                        disableStreamlitShortcuts();
                    }});
                    
                    // Monitor for when chat window opens/closes
                    const observer = new MutationObserver((mutations) => {{
                        const chatWindow = targetDoc.querySelector('df-messenger-chat');
                        if (chatWindow) {{
                            const isMinimized = chatWindow.hasAttribute('minimized');
                            if (!isMinimized) {{
                                // Chat is open - disable shortcuts
                                disableStreamlitShortcuts();
                            }} else {{
                                // Chat is closed - re-enable shortcuts
                                enableStreamlitShortcuts();
                            }}
                        }}
                    }});
                    
                    observer.observe(chatInput, {{
                        attributes: true,
                        childList: true,
                        subtree: true
                    }});
                }}
                
                function disableStreamlitShortcuts() {{
                    // Intercept keyboard events when chat is active
                    if (!targetDoc.dfMessengerKeyHandler) {{
                        targetDoc.dfMessengerKeyHandler = function(e) {{
                            // Check if the event is coming from within the Dialogflow messenger
                            const dfMessenger = targetDoc.querySelector('df-messenger');
                            const dfChat = targetDoc.querySelector('df-messenger-chat');
                            
                            if (document.activeElement && document.activeElement.tagName === 'INPUT') {{
                                // If typing in chat, stop the event from reaching Streamlit
                                if (e.key === 'c' || e.key === 'C' || e.key === 'r' || e.key === 'R') {{
                                    e.stopPropagation();
                                    e.stopImmediatePropagation();
                                }}
                            }}
                        }};
                        
                        // Add listener with high priority (capture phase)
                        targetDoc.addEventListener('keydown', targetDoc.dfMessengerKeyHandler, true);
                        targetDoc.addEventListener('keypress', targetDoc.dfMessengerKeyHandler, true);
                    }}
                }}
                
                function enableStreamlitShortcuts() {{
                    // Remove the keyboard interceptor when chat is closed
                    if (targetDoc.dfMessengerKeyHandler) {{
                        targetDoc.removeEventListener('keydown', targetDoc.dfMessengerKeyHandler, true);
                        targetDoc.removeEventListener('keypress', targetDoc.dfMessengerKeyHandler, true);
                        targetDoc.dfMessengerKeyHandler = null;
                    }}
                }}
                
                // Also handle clicks outside the chat to re-enable shortcuts
                targetDoc.addEventListener('click', (e) => {{
                    const dfMessenger = targetDoc.querySelector('df-messenger');
                    const dfChat = targetDoc.querySelector('df-messenger-chat');
                    
                    if (dfMessenger && !dfMessenger.contains(e.target)) {{
                        // Clicked outside chat - check if chat is minimized
                        if (dfChat && dfChat.hasAttribute('minimized')) {{
                            enableStreamlitShortcuts();
                        }}
                    }}
                }});
                
            }}, 500);
            
        }}, 1000);
    }})();
    </script>
    """
    
    # Remove the key parameter - just use height and width
    components.html(js_code, height=0, width=0)