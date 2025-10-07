# /app/floating_chatbot.py
"""
Floating Chatbot Component for Google Ads Simulator
Mimics Dialogflow Messenger positioning in bottom-right corner
"""

import streamlit as st
import streamlit.components.v1 as components
import random
from typing import List, Dict

class FloatingChatbot:
    def __init__(self):
        self.responses = {
            "campaign": [
                "To create a campaign, go to the Campaign Wizard and follow the step-by-step process.",
                "Start with defining your campaign objective - are you looking for sales, leads, or brand awareness?",
                "Set your daily budget and bidding strategy based on your goals."
            ],
            "keyword": [
                "Use the Keyword Planner to research relevant keywords for your business.",
                "Include a mix of broad, phrase, and exact match keywords.",
                "Consider using negative keywords to exclude irrelevant searches."
            ],
            "budget": [
                "Start with a modest budget and increase based on performance.",
                "Use the Budget Pacing feature to distribute your budget evenly throughout the day.",
                "Monitor your cost per click (CPC) and adjust bids accordingly."
            ],
            "dashboard": [
                "The dashboard shows real-time performance metrics including impressions, clicks, and cost.",
                "Use the auction insights to understand your competitive position.",
                "Check the attribution analysis to see which keywords drive conversions."
            ],
            "help": [
                "I can help you with campaign setup, keyword research, budget management, and performance analysis.",
                "Try asking about specific topics like 'how to create a campaign' or 'keyword research tips'.",
                "Use the Campaign Wizard for guided campaign creation, or explore individual features in the sidebar."
            ]
        }
        
        self.greetings = [
            "Hello! I'm your Google Ads AI assistant. How can I help you today?",
            "Hi there! I'm here to help you with your Google Ads campaigns. What would you like to know?",
            "Welcome! I can assist you with campaign setup, optimization, and analysis. What's on your mind?"
        ]
        
        self.default_responses = [
            "That's a great question! For detailed guidance, I recommend checking the Campaign Wizard or exploring the specific features in the sidebar.",
            "I'd be happy to help! Could you be more specific about what you'd like to know about Google Ads?",
            "Let me point you to the right resources. Try the Keyword Planner for keyword research or the Dashboard for performance insights."
        ]
    
    def get_response(self, user_input: str) -> str:
        """Generate a response based on user input"""
        user_input_lower = user_input.lower()
        
        # Check for greetings
        if any(greeting in user_input_lower for greeting in ["hello", "hi", "hey", "start"]):
            return random.choice(self.greetings)
        
        # Check for specific topics
        for topic, responses in self.responses.items():
            if topic in user_input_lower:
                return random.choice(responses)
        
        # Default response
        return random.choice(self.default_responses)

def render_floating_chatbot():
    """Render a floating chatbot in the bottom-right corner"""
    
    # Initialize session state for chat
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = []
    
    if "chatbot_open" not in st.session_state:
        st.session_state.chatbot_open = False
    
    if "chatbot_instance" not in st.session_state:
        st.session_state.chatbot_instance = FloatingChatbot()
    
    # Chatbot HTML/CSS/JavaScript
    chatbot_html = f"""
    <div id="chatbot-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
        <div id="chatbot-widget" style="
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            display: {'block' if st.session_state.chatbot_open else 'none'};
            border: 1px solid #e0e0e0;
            overflow: hidden;
        ">
            <!-- Chat Header -->
            <div style="
                background: linear-gradient(135deg, #4285F4, #34A853);
                color: white;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600;">🤖 AI Assistant</h3>
                    <p style="margin: 0; font-size: 12px; opacity: 0.9;">Google Ads Helper</p>
                </div>
                <button onclick="toggleChat()" style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    padding: 5px;
                ">×</button>
            </div>
            
            <!-- Chat Messages -->
            <div id="chat-messages" style="
                height: 320px;
                overflow-y: auto;
                padding: 15px;
                background: #f8f9fa;
            ">
                {' '.join([f'''
                <div style="margin-bottom: 10px;">
                    <div style="
                        background: {'#4285F4' if msg['type'] == 'user' else '#e9ecef'};
                        color: {'white' if msg['type'] == 'user' else '#333'};
                        padding: 10px;
                        border-radius: 12px;
                        max-width: 80%;
                        margin-left: {'auto' if msg['type'] == 'user' else '0'};
                        margin-right: {'0' if msg['type'] == 'user' else 'auto'};
                        word-wrap: break-word;
                    ">
                        <strong>{'You' if msg['type'] == 'user' else 'Assistant'}:</strong><br>
                        {msg['content']}
                    </div>
                </div>
                ''' for msg in st.session_state.chatbot_messages])}
            </div>
            
            <!-- Chat Input -->
            <div style="padding: 15px; background: white; border-top: 1px solid #e0e0e0;">
                <div style="display: flex; gap: 10px;">
                    <input type="text" id="chat-input" placeholder="Ask about Google Ads..." style="
                        flex: 1;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 20px;
                        outline: none;
                        font-size: 14px;
                    ">
                    <button onclick="sendMessage()" style="
                        background: #4285F4;
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        cursor: pointer;
                        font-size: 16px;
                    ">→</button>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 5px; flex-wrap: wrap;">
                    <button onclick="quickMessage('campaign')" style="
                        background: #f0f0f0;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        cursor: pointer;
                    ">Campaign</button>
                    <button onclick="quickMessage('keyword')" style="
                        background: #f0f0f0;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        cursor: pointer;
                    ">Keywords</button>
                    <button onclick="quickMessage('budget')" style="
                        background: #f0f0f0;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        cursor: pointer;
                    ">Budget</button>
                    <button onclick="quickMessage('dashboard')" style="
                        background: #f0f0f0;
                        border: none;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 12px;
                        cursor: pointer;
                    ">Dashboard</button>
                </div>
            </div>
        </div>
        
        <!-- Chat Toggle Button -->
        <button onclick="toggleChat()" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #4285F4, #34A853);
            color: white;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(66, 133, 244, 0.4);
            font-size: 24px;
            z-index: 1001;
            display: {'none' if st.session_state.chatbot_open else 'block'};
        ">
            🤖
        </button>
    </div>
    
    <script>
    function toggleChat() {{
        const widget = document.getElementById('chatbot-widget');
        const button = document.querySelector('button[style*="position: fixed"]');
        
        if (widget.style.display === 'none') {{
            widget.style.display = 'block';
            button.style.display = 'none';
        }} else {{
            widget.style.display = 'none';
            button.style.display = 'block';
        }}
    }}
    
    function sendMessage() {{
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (message) {{
            // Send message to Streamlit
            window.parent.postMessage({{
                type: 'chatbot_message',
                message: message
            }}, '*');
            
            input.value = '';
        }}
    }}
    
    function quickMessage(topic) {{
        const messages = {{
            'campaign': 'How do I create a campaign?',
            'keyword': 'Help with keyword research',
            'budget': 'Budget management tips',
            'dashboard': 'How to read the dashboard?'
        }};
        
        window.parent.postMessage({{
            type: 'chatbot_message',
            message: messages[topic]
        }}, '*');
    }}
    
    // Handle Enter key in input
    document.addEventListener('DOMContentLoaded', function() {{
        const input = document.getElementById('chat-input');
        input.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
    }});
    </script>
    """
    
    # Render the chatbot
    components.html(chatbot_html, height=0)
    
    # Handle messages from JavaScript
    if hasattr(st.session_state, 'chatbot_message'):
        user_message = st.session_state.chatbot_message
        if user_message:
            # Add user message
            st.session_state.chatbot_messages.append({
                "type": "user",
                "content": user_message
            })
            
            # Get AI response
            response = st.session_state.chatbot_instance.get_response(user_message)
            
            # Add AI response
            st.session_state.chatbot_messages.append({
                "type": "assistant",
                "content": response
            })
            
            # Clear the message
            st.session_state.chatbot_message = None
            st.rerun()

def handle_chatbot_message():
    """Handle incoming messages from the floating chatbot"""
    # This will be called by the main app to process messages
    pass
