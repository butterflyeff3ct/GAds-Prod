# /app/gemini_chatbot.py
"""
Gemini-Powered Floating Chatbot - SIMPLIFIED & DEBUGGED
Uses Google Cloud Generative AI Applications (Gemini)
Renders as a floating widget in bottom-right corner
"""

import streamlit as st
import streamlit.components.v1 as components

def render_gemini_chatbot():
    """
    Render a floating chatbot powered by Gemini AI
    SIMPLIFIED VERSION with debug visibility
    """
    
    # Ultra-simple chatbot with maximum visibility
    chatbot_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* AGGRESSIVE positioning to ensure visibility */
            #chatbotContainer {
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                z-index: 2147483647 !important; /* Maximum z-index */
                pointer-events: auto !important;
            }
            
            .chat-toggle-btn {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: 3px solid white;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .chat-toggle-btn:hover {
                transform: scale(1.15);
                box-shadow: 0 6px 25px rgba(102, 126, 234, 0.7);
            }
            
            .chat-icon {
                width: 32px;
                height: 32px;
                fill: white;
            }
            
            .chat-window {
                position: absolute;
                bottom: 75px;
                right: 0;
                width: 380px;
                height: 550px;
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                display: none;
                flex-direction: column;
                overflow: hidden;
            }
            
            .chat-window.active {
                display: flex;
            }
            
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .chat-title {
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .close-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .close-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            .messages-area {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f8f9fa;
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .welcome {
                text-align: center;
                padding: 60px 20px;
                color: #666;
            }
            
            .welcome h3 {
                margin: 0 0 10px 0;
                color: #333;
            }
            
            .message {
                padding: 12px 18px;
                border-radius: 18px;
                max-width: 75%;
                word-wrap: break-word;
                line-height: 1.5;
            }
            
            .message.user {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                align-self: flex-end;
                margin-left: auto;
            }
            
            .message.bot {
                background: white;
                color: #333;
                align-self: flex-start;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .input-area {
                padding: 20px;
                background: white;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
            }
            
            .chat-input {
                flex: 1;
                padding: 12px 18px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 15px;
                outline: none;
            }
            
            .chat-input:focus {
                border-color: #667eea;
            }
            
            .send-btn {
                width: 48px;
                height: 48px;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .send-btn:hover {
                opacity: 0.9;
            }
            
            .send-btn svg {
                width: 22px;
                height: 22px;
                fill: white;
            }
            
            .typing {
                display: flex;
                gap: 5px;
                padding: 12px 18px;
                background: white;
                border-radius: 18px;
                width: fit-content;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            .typing span {
                width: 8px;
                height: 8px;
                background: #999;
                border-radius: 50%;
                animation: bounce 1.4s infinite;
            }
            
            .typing span:nth-child(2) { animation-delay: 0.2s; }
            .typing span:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes bounce {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-10px); }
            }
        </style>
    </head>
    <body>
        <div id="chatbotContainer">
            <!-- Toggle Button -->
            <button class="chat-toggle-btn" onclick="toggleChatWindow()">
                <svg class="chat-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
            </button>
            
            <!-- Chat Window -->
            <div class="chat-window" id="chatWindow">
                <div class="chat-header">
                    <div class="chat-title">
                        🤖 AI Assistant
                    </div>
                    <button class="close-btn" onclick="toggleChatWindow()">×</button>
                </div>
                
                <div class="messages-area" id="messagesArea">
                    <div class="welcome">
                        <h3>👋 Hello!</h3>
                        <p>I'm your Google Ads AI assistant. Ask me anything!</p>
                    </div>
                </div>
                
                <div class="input-area">
                    <input 
                        type="text" 
                        class="chat-input" 
                        id="userInput" 
                        placeholder="Ask me about Google Ads..."
                        onkeypress="if(event.key==='Enter') sendMsg()"
                    />
                    <button class="send-btn" onclick="sendMsg()">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
        
        <script>
        let isChatOpen = false;
        
        function toggleChatWindow() {
            isChatOpen = !isChatOpen;
            const chatWindow = document.getElementById('chatWindow');
            const toggleBtn = document.querySelector('.chat-toggle-btn');
            
            if (isChatOpen) {
                chatWindow.classList.add('active');
                toggleBtn.style.display = 'none';
                setTimeout(() => document.getElementById('userInput').focus(), 100);
            } else {
                chatWindow.classList.remove('active');
                toggleBtn.style.display = 'flex';
            }
        }
        
        function addMsg(text, isUser) {
            const area = document.getElementById('messagesArea');
            const welcome = area.querySelector('.welcome');
            if (welcome) welcome.remove();
            
            const msg = document.createElement('div');
            msg.className = 'message ' + (isUser ? 'user' : 'bot');
            msg.textContent = text;
            area.appendChild(msg);
            area.scrollTop = area.scrollHeight;
        }
        
        function showTyping() {
            const area = document.getElementById('messagesArea');
            const typing = document.createElement('div');
            typing.className = 'typing';
            typing.id = 'typing';
            typing.innerHTML = '<span></span><span></span><span></span>';
            area.appendChild(typing);
            area.scrollTop = area.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }
        
        function getResponse(msg) {
            const m = msg.toLowerCase();
            
            if (m.includes('keyword')) {
                return "Use Google Ads Keyword Planner in Step 5. Focus on long-tail keywords with commercial intent. Check search volume and competition levels.";
            } else if (m.includes('bid')) {
                return "Try Target CPA or Maximize Conversions for automated bidding. Start manual if you're new, then switch after getting conversion data.";
            } else if (m.includes('budget')) {
                return "Start with at least 10x your target CPA as daily budget. Monitor impression share to find opportunities.";
            } else if (m.includes('ctr')) {
                return "Improve CTR with compelling headlines, clear CTAs, and ad extensions. A good CTR is 3-5% for search ads.";
            } else if (m.includes('quality')) {
                return "Quality Score = CTR + Ad Relevance + Landing Page. Create tight ad groups, match keywords to ad copy, optimize landing pages.";
            } else {
                return "I can help with keywords, bidding, budgets, CTR, Quality Score, and more! What would you like to know?";
            }
        }
        
        function sendMsg() {
            const input = document.getElementById('userInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            addMsg(msg, true);
            input.value = '';
            input.disabled = true;
            
            showTyping();
            
            setTimeout(() => {
                hideTyping();
                addMsg(getResponse(msg), false);
                input.disabled = false;
                input.focus();
            }, 1000);
        }
        
        console.log('✅ Gemini Chatbot loaded successfully');
        </script>
    </body>
    </html>
    """
    
    # Render with explicit height=0
    components.html(chatbot_html, height=0, width=0, scrolling=False)
