# /app/fallback_chatbot.py
"""
Fallback AI Assistant for when Dialogflow is not configured
Provides basic help and guidance for Google Ads simulator users
"""

import streamlit as st
import random
from typing import List, Dict

class FallbackChatbot:
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

def render_fallback_chat():
    """Render a simple chat interface as fallback for Dialogflow"""
    
    # Initialize session state for chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = FallbackChatbot()
    
    st.subheader("💬 AI Assistant")
    st.info("🤖 Chat with our AI assistant for help with Google Ads campaigns!")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["type"] == "user":
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**Assistant:** {message['content']}")
    
    # Chat input
    user_input = st.text_input("Ask me anything about Google Ads:", key="chat_input")
    
    if st.button("Send", key="send_button") or user_input:
        if user_input.strip():
            # Add user message to history
            st.session_state.chat_history.append({
                "type": "user",
                "content": user_input
            })
            
            # Get AI response
            response = st.session_state.chatbot.get_response(user_input)
            
            # Add AI response to history
            st.session_state.chat_history.append({
                "type": "assistant", 
                "content": response
            })
            
            # Clear input and rerun
            st.rerun()
    
    # Quick action buttons
    st.markdown("**Quick Actions:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Dashboard Help", key="dashboard_help"):
            st.session_state.chat_history.append({
                "type": "user",
                "content": "dashboard"
            })
            st.session_state.chat_history.append({
                "type": "assistant",
                "content": random.choice(st.session_state.chatbot.responses["dashboard"])
            })
            st.rerun()
    
    with col2:
        if st.button("🎯 Campaign Setup", key="campaign_help"):
            st.session_state.chat_history.append({
                "type": "user",
                "content": "campaign"
            })
            st.session_state.chat_history.append({
                "type": "assistant",
                "content": random.choice(st.session_state.chatbot.responses["campaign"])
            })
            st.rerun()
    
    with col3:
        if st.button("🔍 Keywords", key="keyword_help"):
            st.session_state.chat_history.append({
                "type": "user",
                "content": "keyword"
            })
            st.session_state.chat_history.append({
                "type": "assistant",
                "content": random.choice(st.session_state.chatbot.responses["keyword"])
            })
            st.rerun()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()
    
    # Tips section
    with st.expander("💡 Tips for Better Results"):
        st.markdown("""
        **Ask specific questions like:**
        - "How do I set up my first campaign?"
        - "What keywords should I use?"
        - "How much should I budget?"
        - "How do I read the dashboard?"
        
        **Or try these topics:**
        - Campaign optimization
        - Keyword research
        - Budget management
        - Performance analysis
        """)
