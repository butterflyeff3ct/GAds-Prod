"""
reCAPTCHA Integration Module
Provides bot protection for signup forms using Google reCAPTCHA v2
"""

import streamlit as st
import streamlit.components.v1 as components
import requests
from typing import Optional, Tuple


class ReCaptchaManager:
    """Manages reCAPTCHA validation for forms"""
    
    def __init__(self):
        """Initialize reCAPTCHA manager with settings from secrets"""
        try:
            recaptcha_config = st.secrets.get("recaptcha", {})
            
            self.enabled = recaptcha_config.get("enabled", False)
            self.site_key = recaptcha_config.get("site_key", "")
            self.secret_key = recaptcha_config.get("secret_key", "")
            self.version = recaptcha_config.get("version", "v2")  # v2 or v3
            
            # Validate configuration
            if self.enabled and (not self.site_key or not self.secret_key):
                print("[WARNING] reCAPTCHA enabled but keys missing")
                self.enabled = False
            
            # Validation endpoint
            self.verify_url = "https://www.google.com/recaptcha/api/siteverify"
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize reCAPTCHA: {e}")
            self.enabled = False
    
    def render_recaptcha(self, key: str = "recaptcha_response") -> Optional[str]:
        """
        Render reCAPTCHA v2 widget in the page
        
        Args:
            key: Unique key for this reCAPTCHA instance
        
        Returns:
            reCAPTCHA response token (will be validated server-side)
        """
        if not self.enabled:
            return None
        
        # Create unique container ID
        container_id = f"recaptcha-{key}"
        
        # JavaScript to render reCAPTCHA and store response
        recaptcha_html = f"""
        <div id="{container_id}"></div>
        
        <script src="https://www.google.com/recaptcha/api.js?onload=onloadCallback&render=explicit" async defer></script>
        
        <script type="text/javascript">
            var onloadCallback = function() {{
                grecaptcha.render('{container_id}', {{
                    'sitekey': '{self.site_key}',
                    'callback': function(response) {{
                        // Store response in Streamlit
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            key: '{key}',
                            value: response
                        }}, '*');
                    }},
                    'expired-callback': function() {{
                        // Clear response if expired
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            key: '{key}',
                            value: ''
                        }}, '*');
                    }}
                }});
            }};
        </script>
        
        <style>
            #{container_id} {{
                display: flex;
                justify-content: center;
                margin: 20px 0;
            }}
        </style>
        """
        
        # Render the component
        response = components.html(recaptcha_html, height=78)
        
        return response
    
    def verify_recaptcha(self, response_token: str) -> Tuple[bool, str]:
        """
        Verify reCAPTCHA response with Google's servers
        
        Args:
            response_token: Token received from reCAPTCHA widget
        
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        if not self.enabled:
            # If disabled, always return True (backward compatibility)
            return True, ""
        
        if not response_token:
            return False, "Please complete the reCAPTCHA verification"
        
        try:
            # Send verification request to Google
            payload = {
                'secret': self.secret_key,
                'response': response_token
            }
            
            response = requests.post(self.verify_url, data=payload)
            result = response.json()
            
            if result.get('success'):
                return True, ""
            else:
                error_codes = result.get('error-codes', [])
                print(f"[ERROR] reCAPTCHA verification failed: {error_codes}")
                
                # User-friendly error messages
                if 'timeout-or-duplicate' in error_codes:
                    return False, "reCAPTCHA expired. Please try again."
                elif 'invalid-input-response' in error_codes:
                    return False, "Invalid reCAPTCHA. Please try again."
                else:
                    return False, "reCAPTCHA verification failed. Please try again."
            
        except requests.RequestException as e:
            print(f"[ERROR] reCAPTCHA network error: {e}")
            return False, "Network error during verification. Please try again."
        except Exception as e:
            print(f"[ERROR] reCAPTCHA validation error: {e}")
            return False, "Verification error. Please try again."
    
    def verify_recaptcha_v3(self, response_token: str, action: str = "signup", 
                           threshold: float = 0.5) -> Tuple[bool, str, float]:
        """
        Verify reCAPTCHA v3 response (score-based)
        
        Args:
            response_token: Token from reCAPTCHA v3
            action: Action name for verification
            threshold: Minimum score required (0.0 to 1.0)
        
        Returns:
            Tuple of (success: bool, error_message: str, score: float)
        """
        if not self.enabled:
            return True, "", 1.0
        
        if not response_token:
            return False, "reCAPTCHA verification required", 0.0
        
        try:
            payload = {
                'secret': self.secret_key,
                'response': response_token
            }
            
            response = requests.post(self.verify_url, data=payload)
            result = response.json()
            
            if result.get('success'):
                score = result.get('score', 0.0)
                
                if score >= threshold:
                    return True, "", score
                else:
                    print(f"[WARNING] Low reCAPTCHA score: {score}")
                    return False, f"Suspicious activity detected. Please try again.", score
            else:
                error_codes = result.get('error-codes', [])
                print(f"[ERROR] reCAPTCHA v3 verification failed: {error_codes}")
                return False, "reCAPTCHA verification failed", 0.0
            
        except Exception as e:
            print(f"[ERROR] reCAPTCHA v3 validation error: {e}")
            return False, "Verification error", 0.0


# Convenience function
def get_recaptcha_manager() -> ReCaptchaManager:
    """Get or create ReCaptchaManager instance"""
    if 'recaptcha_manager' not in st.session_state:
        st.session_state.recaptcha_manager = ReCaptchaManager()
    return st.session_state.recaptcha_manager
