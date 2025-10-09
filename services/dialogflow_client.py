# /services/dialogflow_client.py
import streamlit as st

@st.cache_resource
def get_dialogflow_client():
    """Initializes a mock Dialogflow client."""
    return DialogflowClient()

class DialogflowClient:
    """
    A mock Dialogflow client that returns canned responses.
    Replace this with the actual Google Dialogflow SDK implementation if needed.
    """
    def __init__(self):
        print("ℹ️ Initialized Mock Dialogflow Client.")
        self.canned_responses = [
            "That's a great question! For that, I would recommend reviewing your Search Terms Report to find new negative keywords.",
            "To improve your Click-Through Rate (CTR), try adding more compelling headlines to your ads and test different calls-to-action.",
            "Based on your campaign goals, a 'Target CPA' bidding strategy might be effective.",
            "Consider adding sitelink extensions to your ads to provide more links to your site and improve ad rank."
        ]

    def detect_intent(self, text: str, session_id: str, parameters: dict = None) -> dict:
        """Simulates detecting an intent and returns a deterministic response."""
        # Use session_id hash for deterministic response selection
        response_index = hash(session_id) % len(self.canned_responses)
        response_text = self.canned_responses[response_index]
        return {"response_text": response_text}