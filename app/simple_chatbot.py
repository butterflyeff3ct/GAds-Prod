# /app/simple_chatbot.py
"""
Lightweight Chatbot for Google Ads Simulator
Memory-optimized version with minimal resource usage
"""

import streamlit as st
import streamlit.components.v1 as components

def render_simple_chatbot():
    """Render a simple, memory-efficient chatbot"""
    
    # Initialize minimal session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Limit chat history to prevent memory bloat
    if len(st.session_state.chat_history) > 10:
        st.session_state.chat_history = st.session_state.chat_history[-10:]
    
    # Simple chatbot HTML (minimal memory footprint)
    chatbot_html = """
    <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <div id="chat-widget" style="
            width: 300px;
            height: 400px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border: 1px solid #ddd;
            display: none;
        ">
            <div style="background: #4285F4; color: white; padding: 10px; border-radius: 8px 8px 0 0;">
                <h4 style="margin: 0;">🤖 AI Assistant</h4>
            </div>
            <div id="chat-messages" style="height: 300px; overflow-y: auto; padding: 10px; background: #f8f9fa;">
                <div style="color: #666; font-size: 14px;">
                    Hi! I can help you with Google Ads campaigns, keywords, and optimization.
                </div>
            </div>
            <div style="padding: 10px; border-top: 1px solid #ddd;">
                <input type="text" id="chat-input" placeholder="Ask about Google Ads..." style="
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-bottom: 5px;
                ">
                <div style="display: flex; gap: 5px;">
                    <button onclick="sendMessage()" style="
                        background: #4285F4;
                        color: white;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 4px;
                        cursor: pointer;
                        flex: 1;
                    ">Send</button>
                    <button onclick="toggleChat()" style="
                        background: #ccc;
                        color: #333;
                        border: none;
                        padding: 8px 15px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">Close</button>
                </div>
            </div>
        </div>
        
        <button onclick="toggleChat()" style="
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #4285F4;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 20px;
            box-shadow: 0 2px 8px rgba(66, 133, 244, 0.3);
        ">🤖</button>
    </div>
    
    <script>
    function toggleChat() {
        const widget = document.getElementById('chat-widget');
        if (widget.style.display === 'none') {
            widget.style.display = 'block';
        } else {
            widget.style.display = 'none';
        }
    }
    
    function sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        if (message) {
            // Add user message
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += '<div style="background: #e3f2fd; padding: 8px; margin: 5px 0; border-radius: 4px;"><strong>You:</strong> ' + message + '</div>';
            
            // Simple response logic
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
            
            messagesDiv.innerHTML += '<div style="background: #f0f0f0; padding: 8px; margin: 5px 0; border-radius: 4px;"><strong>Assistant:</strong> ' + response + '</div>';
            
            // Scroll to bottom
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Clear input
            input.value = '';
        }
    }
    
    // Handle Enter key
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
    
    # Render the lightweight chatbot
    components.html(chatbot_html, height=0)
