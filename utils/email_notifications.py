"""
Email Notification System for User Management
Sends approval/denial emails using Gmail SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from typing import Optional


class EmailNotifier:
    """Handles email notifications for user management events"""
    
    def __init__(self):
        """Initialize email notifier with Gmail SMTP settings"""
        try:
            email_config = st.secrets.get("email_notifications", {})
            
            self.enabled = email_config.get("enabled", False)
            self.smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
            self.smtp_port = email_config.get("smtp_port", 587)
            self.sender_email = email_config.get("sender_email", "")
            self.sender_password = email_config.get("sender_password", "")
            self.sender_name = email_config.get("sender_name", "Google Ads Simulator")
            
            # Validate configuration
            if self.enabled and (not self.sender_email or not self.sender_password):
                print("[WARNING] Email notifications enabled but credentials missing")
                self.enabled = False
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize email notifier: {e}")
            self.enabled = False
    
    def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
        """
        Send an email using Gmail SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text fallback (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"[INFO] Email notifications disabled - would have sent to {to_email}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text version (fallback)
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS encryption
            
            # Login
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            print(f"[SUCCESS] Email sent to {to_email}: {subject}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"[ERROR] SMTP Authentication failed - check email/password")
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error sending email: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False
    
    def send_approval_email(self, to_email: str, user_name: str, user_id: str) -> bool:
        """Send approval notification email"""
        
        subject = "✅ Your Access Request Has Been Approved!"
        
        # HTML version
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">🎉 Welcome to Google Ads Simulator!</h2>
                
                <p>Hi {user_name},</p>
                
                <p>Great news! Your access request has been <strong>approved</strong>.</p>
                
                <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Your User ID:</strong> {user_id}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Status:</strong> Approved ✅</p>
                </div>
                
                <h3>What's Next?</h3>
                <ol>
                    <li>Visit the <a href="https://your-app-url.streamlit.app" style="color: #007bff;">Google Ads Simulator</a></li>
                    <li>Click "Sign in with Google"</li>
                    <li>Use the email address: <strong>{to_email}</strong></li>
                    <li>Start learning Google Ads campaign management!</li>
                </ol>
                
                <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>💡 Tip:</strong> Save your User ID for reference. You can find it in your profile once logged in.</p>
                </div>
                
                <h3>Need Help?</h3>
                <p>If you have any questions or encounter any issues, feel free to reach out:</p>
                <ul>
                    <li>📧 Email: <a href="mailto:admin@yourdomain.com" style="color: #007bff;">admin@yourdomain.com</a></li>
                </ul>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="color: #6c757d; font-size: 14px;">
                    This is an automated message from Google Ads Simulator.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        body_text = f"""
        Welcome to Google Ads Simulator!
        
        Hi {user_name},
        
        Great news! Your access request has been approved.
        
        Your User ID: {user_id}
        Status: Approved
        
        What's Next?
        1. Visit the Google Ads Simulator
        2. Click "Sign in with Google"
        3. Use the email address: {to_email}
        4. Start learning Google Ads campaign management!
        
        Need Help?
        Email: admin@yourdomain.com
        
        ---
        This is an automated message. Please do not reply.
        """
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def send_denial_email(self, to_email: str, user_name: str, user_id: str, 
                         denial_reason: str, can_reapply: bool = True) -> bool:
        """Send denial notification email"""
        
        subject = "❌ Update on Your Access Request"
        
        reapply_text = ""
        if can_reapply:
            reapply_text = """
            <h3>Can I Reapply?</h3>
            <p>Yes! If you believe this issue has been resolved, you're welcome to submit a new access request. You can reapply up to 3 times.</p>
            <p><a href="https://your-app-url.streamlit.app" style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reapply for Access</a></p>
            """
        else:
            reapply_text = """
            <p>You have reached the maximum number of reapplication attempts. If you believe this is an error, please contact the administrator directly.</p>
            """
        
        # HTML version
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc3545;">Update on Your Access Request</h2>
                
                <p>Hi {user_name},</p>
                
                <p>Thank you for your interest in the Google Ads Simulator. After reviewing your request, we're unable to approve your access at this time.</p>
                
                <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Your User ID:</strong> {user_id}</p>
                    <p style="margin: 10px 0 0 0;"><strong>Status:</strong> Not Approved</p>
                    <p style="margin: 10px 0 0 0;"><strong>Reason:</strong> {denial_reason}</p>
                </div>
                
                {reapply_text}
                
                <h3>Need Help?</h3>
                <p>If you have questions about this decision or need assistance, please contact us:</p>
                <ul>
                    <li>📧 Email: <a href="mailto:admin@yourdomain.com" style="color: #007bff;">admin@yourdomain.com</a></li>
                    <li>Include your User ID: <strong>{user_id}</strong></li>
                </ul>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="color: #6c757d; font-size: 14px;">
                    This is an automated message from Google Ads Simulator.<br>
                    Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        body_text = f"""
        Update on Your Access Request
        
        Hi {user_name},
        
        Thank you for your interest in the Google Ads Simulator. After reviewing your request, we're unable to approve your access at this time.
        
        Your User ID: {user_id}
        Status: Not Approved
        Reason: {denial_reason}
        
        {'You can reapply if you believe this issue has been resolved.' if can_reapply else 'You have reached the maximum reapplication attempts.'}
        
        Need Help?
        Email: admin@yourdomain.com
        Include your User ID: {user_id}
        
        ---
        This is an automated message. Please do not reply.
        """
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration"""
        
        subject = "🧪 Test Email from Google Ads Simulator"
        
        body_html = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #28a745;">✅ Email Configuration Test</h2>
                <p>If you're reading this, your email notifications are working correctly!</p>
                <p>This is a test email from the Google Ads Simulator notification system.</p>
            </div>
        </body>
        </html>
        """
        
        body_text = "Email Configuration Test - If you're reading this, your email notifications are working!"
        
        return self.send_email(to_email, subject, body_html, body_text)


# Convenience function for easy import
def get_email_notifier() -> EmailNotifier:
    """Get or create EmailNotifier instance"""
    if 'email_notifier' not in st.session_state:
        st.session_state.email_notifier = EmailNotifier()
    return st.session_state.email_notifier
