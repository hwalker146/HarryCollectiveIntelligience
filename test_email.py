#!/usr/bin/env python3
"""
Test email configuration to debug Gmail authentication
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_email_config():
    """Test email configuration with detailed error reporting"""
    
    # Get environment variables
    sender_email = os.getenv('EMAIL_USER', 'aipodcastdigest@gmail.com')
    sender_password = os.getenv('EMAIL_PASSWORD')
    recipient_email = 'hwalker146@outlook.com'
    
    print(f"📧 Testing email configuration...")
    print(f"📤 Sender email: {sender_email}")
    print(f"📥 Recipient email: {recipient_email}")
    print(f"🔑 Password configured: {'✅ Yes' if sender_password else '❌ No'}")
    
    if not sender_password:
        print("❌ EMAIL_PASSWORD not found in environment")
        return False
    
    # Check for common app password issues
    if len(sender_password) != 16:
        print(f"⚠️ App password length: {len(sender_password)} (should be 16 characters)")
    
    if ' ' in sender_password:
        print("⚠️ App password contains spaces - this might cause issues")
        sender_password = sender_password.replace(' ', '')
        print(f"🔧 Removed spaces, new length: {len(sender_password)}")
    
    # Create test email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = "Test Email - Podcast System"
    
    test_content = """
    This is a test email from the automated podcast system.
    
    If you receive this, email authentication is working correctly.
    
    System Status: Testing
    Date: 2025-08-11
    """
    
    msg.attach(MIMEText(test_content, 'plain'))
    
    try:
        print("🔄 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        
        print("🔄 Starting TLS encryption...")
        server.starttls()
        
        print("🔄 Attempting login...")
        server.login(sender_email, sender_password)
        
        print("🔄 Sending test email...")
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print("✅ Email sent successfully!")
        print(f"📧 Check {recipient_email} for the test message")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("\n💡 Troubleshooting steps:")
        print("1. Verify 2-factor authentication is enabled on Gmail")
        print("2. Regenerate app password at: https://myaccount.google.com/apppasswords")
        print("3. Make sure EMAIL_USER matches the Gmail account that created the app password")
        print("4. App password should be 16 characters with no spaces")
        return False
        
    except Exception as e:
        print(f"❌ Email failed with error: {e}")
        return False

if __name__ == "__main__":
    test_email_config()