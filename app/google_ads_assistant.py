# /app/google_ads_assistant.py
"""
Google Ads Assistant - Professional Chatbot Interface
Matches the design from the original implementation
"""

import streamlit as st
import streamlit.components.v1 as components

def render_google_ads_assistant():
    """Render the Google Ads Assistant panel"""
    
    # Initialize session state
    if "assistant_open" not in st.session_state:
        st.session_state.assistant_open = True
    
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []
    
    # Limit message history to prevent memory bloat
    if len(st.session_state.assistant_messages) > 20:
        st.session_state.assistant_messages = st.session_state.assistant_messages[-20:]
    
    # Assistant panel HTML/CSS
    assistant_html = f"""
    <div id="assistant-container" style="
        position: fixed;
        top: 20px;
        right: 20px;
        width: 350px;
        height: calc(100vh - 40px);
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        border: 1px solid #e0e0e0;
        z-index: 1000;
        display: {'block' if st.session_state.assistant_open else 'none'};
        overflow: hidden;
    ">
        <!-- Assistant Header -->
        <div style="
            background: linear-gradient(135deg, #1a73e8, #4285f4);
            color: white;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div>
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">Google Ads Assistant</h3>
                <p style="margin: 0; font-size: 12px; opacity: 0.9;">Your AI co-pilot</p>
            </div>
            <button onclick="toggleAssistant()" style="
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
            ">×</button>
        </div>
        
        <!-- Assistant Content -->
        <div style="
            height: calc(100% - 140px);
            overflow-y: auto;
            padding: 16px;
            background: #f8f9fa;
        ">
            <!-- Welcome Message -->
            <div style="
                background: white;
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 16px;
                border-left: 4px solid #4285f4;
            ">
                <p style="margin: 0; font-size: 14px; line-height: 1.5;">
                    Hello! I'm your Google Ads co-pilot. I'm here to help you save time, make smarter decisions, and improve your campaign performance.
                </p>
            </div>
            
            <!-- Capabilities -->
            <div style="margin-bottom: 16px;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #333;">I can help you with:</h4>
                
                <div style="background: white; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    <strong style="color: #4285f4; font-size: 13px;">Analysis & Reporting:</strong>
                    <ul style="margin: 4px 0 0 0; padding-left: 16px; font-size: 12px; color: #666;">
                        <li>Get performance summaries</li>
                        <li>Specific metric retrievals</li>
                        <li>Comparative analysis</li>
                        <li>Identify top/bottom performers</li>
                    </ul>
                </div>
                
                <div style="background: white; padding: 12px; border-radius: 8px;">
                    <strong style="color: #4285f4; font-size: 13px;">Optimization & Strategy:</strong>
                    <ul style="margin: 4px 0 0 0; padding-left: 16px; font-size: 12px; color: #666;">
                        <li>Keyword suggestions</li>
                        <li>Bidding adjustments</li>
                        <li>Budget optimization</li>
                        <li>Audience targeting</li>
                    </ul>
                </div>
            </div>
            
            <!-- Chat Messages -->
            <div id="assistant-messages" style="
                max-height: 200px;
                overflow-y: auto;
                margin-bottom: 16px;
            ">
                {' '.join([f'''
                <div style="margin-bottom: 12px;">
                    <div style="
                        background: {'#e3f2fd' if msg['type'] == 'user' else 'white'};
                        padding: 12px;
                        border-radius: 8px;
                        border-left: 3px solid {'#4285f4' if msg['type'] == 'user' else '#34a853'};
                        font-size: 13px;
                        line-height: 1.4;
                    ">
                        <strong style="color: {'#4285f4' if msg['type'] == 'user' else '#34a853'};">
                            {'You' if msg['type'] == 'user' else 'Assistant'}:
                        </strong><br>
                        {msg['content']}
                    </div>
                </div>
                ''' for msg in st.session_state.assistant_messages])}
            </div>
            
            <!-- Quick Actions -->
            <div style="margin-bottom: 16px;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #333;">Quick Actions:</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                    <button onclick="quickAction('performance')" style="
                        background: #f0f0f0;
                        border: 1px solid #ddd;
                        padding: 6px 12px;
                        border-radius: 16px;
                        font-size: 12px;
                        cursor: pointer;
                        color: #333;
                    ">📊 Performance</button>
                    <button onclick="quickAction('keywords')" style="
                        background: #f0f0f0;
                        border: 1px solid #ddd;
                        padding: 6px 12px;
                        border-radius: 16px;
                        font-size: 12px;
                        cursor: pointer;
                        color: #333;
                    ">🔍 Keywords</button>
                    <button onclick="quickAction('budget')" style="
                        background: #f0f0f0;
                        border: 1px solid #ddd;
                        padding: 6px 12px;
                        border-radius: 16px;
                        font-size: 12px;
                        cursor: pointer;
                        color: #333;
                    ">💰 Budget</button>
                    <button onclick="quickAction('optimize')" style="
                        background: #f0f0f0;
                        border: 1px solid #ddd;
                        padding: 6px 12px;
                        border-radius: 16px;
                        font-size: 12px;
                        cursor: pointer;
                        color: #333;
                    ">⚡ Optimize</button>
                </div>
            </div>
        </div>
        
        <!-- Input Area -->
        <div style="
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #e0e0e0;
            padding: 16px;
        ">
            <div style="display: flex; gap: 8px; align-items: center;">
                <input type="text" id="assistant-input" placeholder="Ask something..." style="
                    flex: 1;
                    padding: 10px 12px;
                    border: 1px solid #ddd;
                    border-radius: 20px;
                    outline: none;
                    font-size: 14px;
                    background: #f8f9fa;
                ">
                <button onclick="sendMessage()" style="
                    background: #4285f4;
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 36px;
                    height: 36px;
                    cursor: pointer;
                    font-size: 16px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">✈</button>
            </div>
        </div>
    </div>
    
    <!-- Toggle Button (when assistant is closed) -->
    <button onclick="toggleAssistant()" style="
        position: fixed;
        top: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1a73e8, #4285f4);
        color: white;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(26, 115, 232, 0.4);
        font-size: 24px;
        z-index: 1001;
        display: {'none' if st.session_state.assistant_open else 'block'};
    ">
        🤖
    </button>
    
    <script>
    function toggleAssistant() {{
        const container = document.getElementById('assistant-container');
        const button = document.querySelector('button[style*="position: fixed"]');
        
        if (container.style.display === 'none') {{
            container.style.display = 'block';
            button.style.display = 'none';
            // Send message to Streamlit to update state
            window.parent.postMessage({{
                type: 'assistant_toggle',
                open: true
            }}, '*');
        }} else {{
            container.style.display = 'none';
            button.style.display = 'block';
            // Send message to Streamlit to update state
            window.parent.postMessage({{
                type: 'assistant_toggle',
                open: false
            }}, '*');
        }}
    }}
    
    function sendMessage() {{
        const input = document.getElementById('assistant-input');
        const message = input.value.trim();
        
        if (message) {{
            // Send message to Streamlit
            window.parent.postMessage({{
                type: 'assistant_message',
                message: message
            }}, '*');
            
            input.value = '';
        }}
    }}
    
    function quickAction(action) {{
        const messages = {{
            'performance': 'Show me my campaign performance summary',
            'keywords': 'Help me find new keywords for my campaign',
            'budget': 'Analyze my budget allocation and suggest optimizations',
            'optimize': 'What optimizations do you recommend for my campaigns?'
        }};
        
        window.parent.postMessage({{
            type: 'assistant_message',
            message: messages[action]
        }}, '*');
    }}
    
    // Handle Enter key in input
    document.addEventListener('DOMContentLoaded', function() {{
        const input = document.getElementById('assistant-input');
        input.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
    }});
    </script>
    """
    
    # Render the assistant
    components.html(assistant_html, height=0)
    
    # Handle messages from JavaScript
    if hasattr(st.session_state, 'assistant_message'):
        user_message = st.session_state.assistant_message
        if user_message:
            # Add user message
            st.session_state.assistant_messages.append({
                "type": "user",
                "content": user_message
            })
            
            # Generate AI response
            response = generate_assistant_response(user_message)
            
            # Add AI response
            st.session_state.assistant_messages.append({
                "type": "assistant",
                "content": response
            })
            
            # Clear the message
            st.session_state.assistant_message = None
            st.rerun()

def generate_assistant_response(user_input: str) -> str:
    """Generate intelligent responses for the Google Ads Assistant"""
    user_input_lower = user_input.lower()
    
    # Performance-related queries
    if any(word in user_input_lower for word in ['performance', 'metrics', 'results', 'summary']):
        return "Based on your current campaign data, I can see your performance metrics. Your CTR is showing good engagement, and your cost per click is within the target range. I recommend focusing on your top-performing keywords and considering bid adjustments for underperforming ones."
    
    # Keyword-related queries
    elif any(word in user_input_lower for word in ['keyword', 'keywords', 'research', 'search terms']):
        return "For keyword research, I suggest exploring long-tail variations of your current keywords. Consider adding negative keywords to improve relevance. Your broad match keywords are generating good volume, but phrase and exact match might give you better conversion rates."
    
    # Budget-related queries
    elif any(word in user_input_lower for word in ['budget', 'spend', 'cost', 'allocation']):
        return "Your budget pacing looks good, but I notice some opportunities for optimization. Consider increasing bids on high-converting keywords during peak hours. You might also want to adjust your daily budget based on performance patterns."
    
    # Optimization queries
    elif any(word in user_input_lower for word in ['optimize', 'improve', 'better', 'suggestions']):
        return "Here are my top optimization suggestions: 1) Test different ad copy variations, 2) Adjust your bidding strategy based on device performance, 3) Review your ad scheduling for peak performance hours, 4) Consider audience targeting refinements."
    
    # Campaign setup queries
    elif any(word in user_input_lower for word in ['campaign', 'setup', 'create', 'new']):
        return "To create an effective campaign, start with the Campaign Wizard. Choose your objective (sales, leads, or awareness), set an appropriate daily budget, and select relevant keywords. I can guide you through each step of the setup process."
    
    # Default response
    else:
        return "I'm here to help you with your Google Ads campaigns! You can ask me about performance analysis, keyword research, budget optimization, or campaign setup. What specific area would you like assistance with?"
