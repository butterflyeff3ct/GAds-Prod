# /services/chatbot_client.py
"""
Chatbot Client for Google Cloud Generative AI Applications
Uses Gemini API for conversational assistance
"""
import streamlit as st
from services.gemini_client import get_gemini_client

@st.cache_resource
def get_chatbot_client():
    """Get the Gemini-powered chatbot client"""
    return ChatbotClient()

class ChatbotClient:
    """
    Gemini AI-powered chatbot for Google Ads assistance
    Provides contextual help and guidance throughout the simulator
    """
    def __init__(self):
        self.gemini = get_gemini_client()
        self.system_context = """You are a helpful Google Ads expert assistant integrated into a Google Ads Campaign Simulator.
        
Your role:
- Help users understand Google Ads concepts
- Provide optimization tips and best practices
- Explain bidding strategies, keywords, and campaign structure
- Give concise, actionable advice (2-3 sentences)
- Be friendly and encouraging

Keep responses brief and focused."""

    def get_response(self, user_message: str, conversation_history: list = None) -> str:
        """
        Get AI response to user message
        
        Args:
            user_message: User's question
            conversation_history: Previous messages for context
            
        Returns:
            AI-generated response
        """
        try:
            # Build context
            full_prompt = self.system_context + "\n\n"
            
            if conversation_history:
                for msg in conversation_history[-5:]:  # Last 5 for context
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    full_prompt += f"{role}: {content}\n"
            
            full_prompt += f"user: {user_message}\nassistant:"
            
            # Get response from Gemini
            if self.gemini.use_real_api:
                response = self.gemini.model.generate_content(full_prompt)
                return response.text.strip()
            else:
                # Fallback to contextual responses
                return self._get_contextual_fallback(user_message)
                
        except Exception as e:
            return "I'm having trouble connecting right now. Please try again."
    
    def _get_contextual_fallback(self, message: str) -> str:
        """Smart contextual responses when API unavailable"""
        msg = message.lower()
        
        keywords_response = {
            'keyword': "For keyword research, use Google Ads Keyword Planner. Focus on long-tail keywords with commercial intent. Check search volume and competition levels.",
            'bid': "Consider automated bidding strategies like Target CPA or Maximize Conversions. Start with manual bidding if you're new, then switch to automated after getting conversion data.",
            'budget': "Start with at least 10x your target CPA as daily budget. This gives Google's algorithm enough data to optimize. Monitor impression share to identify missed opportunities.",
            'ctr': "Improve CTR with compelling headlines, clear CTAs, and ad extensions. Test multiple ad variations. A good CTR for search ads is 3-5%.",
            'quality': "Quality Score depends on expected CTR, ad relevance, and landing page experience. Create tight ad groups, match keywords to ad copy, and optimize landing pages.",
            'extension': "Use sitelinks, callouts, structured snippets, and call extensions. They're free and boost CTR by 10-15%. More extensions = better ad rank.",
            'conversion': "Set up conversion tracking first! Define what counts as a conversion, install the tracking tag, and test it before launching campaigns.",
            'negative': "Check Search Terms Report weekly. Add negative keywords to prevent wasted spend. Use broad match negatives for categories, exact match for specific terms.",
        }
        
        for keyword, response in keywords_response.items():
            if keyword in msg:
                return response
        
        return "I can help with keywords, bidding, budgets, CTR optimization, Quality Score, ad extensions, conversions, and more! What would you like to know?"
